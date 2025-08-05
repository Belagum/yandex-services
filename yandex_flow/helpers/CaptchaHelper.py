import base64, io, re, time, asyncio, requests
from typing import Optional, Tuple, List, Union
from PIL import Image

from app_utils.storage import JsonStore
from app_utils.utils import SETTINGS_FILE
from .BaseHelper import BaseHelper


class CaptchaHelper(BaseHelper):
    X_SMART_CONT   = '//*[@data-testid="silhouette-container"]'
    X_SMART_FORM   = '//form[contains(@id,"advanced-captcha")]'
    X_CAPTCHA_IMG  = '//*[@id="advanced-captcha-form"]//img'
    X_TEXT_LABEL   = '//*[@id="advanced-captcha-form"]//label'
    X_TEXT_INPUT   = '//*[@id="advanced-captcha-form"]//input[@name="rep"]'
    X_SUBMIT_BTN   = '//button[@data-testid="submit"]'

    LOC_CHECKBOX_FORM = (
        '//div[contains(@class,"captcha__checkbox")]'
        ' | //div[contains(@class,"CheckboxCaptcha-Anchor")]'
    )

    LOC_CHECKBOX_BTN = (
        '#js-button'
    )

    LOC_ADVANCED_FORM = (
        '//form[contains(@id,"advanced-captcha")]'
        ' | //form[contains(@class,"AdvancedCaptcha-View")]'
    )

    def __init__(self, page):
        super().__init__(page)
        cfg_all  = JsonStore(SETTINGS_FILE).load()
        cfg = cfg_all.get("captcha", {})
        self.api_2captcha = cfg.get("2captcha_api_key")
        self.api_capsola = cfg.get("capsola_api_key")
        raw = (cfg.get("captcha_service") or "").lower().strip()
        for svc in (raw, "capsola", "2captcha"):
            if getattr(self, f"api_{svc}", None):
                self.solver = svc
                break
        else:
            self.solver = None

    async def solve(self) -> None:
        if not await self._detect_any(): return
        if not self.solver: raise RuntimeError("No captcha solver configured")
        rounds = 3
        for _ in range(rounds):
            if await self._try_checkbox():
                if not await self._detect_any(): return
                continue
            for _ in range(6):
                solved, msg = await self._solve_advanced()
                if solved is None:
                    await self.page.reload(wait_until="domcontentloaded")
                    await self.page.wait_for_timeout(5_000)
                    await self.click(self.LOC_CHECKBOX_BTN)
                    continue
                if solved:
                    break
                raise Exception(f"captcha solve error: {msg}")
            else:
                raise Exception("captcha could not be solved (6 attempts)")
            if not await self._detect_any(): return
        raise Exception(f"captcha reappeared after {rounds} solves")

    async def _detect_any(self) -> bool:
        for x in (
            self.LOC_CHECKBOX_FORM,
            self.LOC_ADVANCED_FORM,
            self.X_SMART_CONT,
            self.X_CAPTCHA_IMG,
        ):
            if await self.is_present(x, wait=False):
                return True
        return False

    async def _detect_smart(self) -> bool:
        return await self.is_present(self.X_SMART_CONT, wait=False)

    async def _detect_text(self) -> bool:
        return (
            not await self._detect_smart()
            and await self.is_present(self.X_CAPTCHA_IMG, wait=False)
            and await self.is_present(self.X_TEXT_INPUT, wait=False)
        )

    async def _try_checkbox(self) -> bool:
        if not await self.is_present(self.LOC_CHECKBOX_FORM, wait=False):
            return False
        await self.click(self.LOC_CHECKBOX_BTN)

        # ждём исчезновения или появления расширенной формы
        for _ in range(20):
            await self.page.wait_for_timeout(1_000)
            if (
                await self.is_present(self.LOC_ADVANCED_FORM, wait=False)
                or await self._detect_smart()
                or await self._detect_text()
            ):
                return False

        # чекбокс исчез полностью, капчи больше нет
        if not await self.is_present(self.LOC_CHECKBOX_FORM, wait=False):
            return True
        return False

    async def _extract_key(self) -> Optional[str]:
        form = await self.page.wait_for_selector(
            f"xpath={self.X_SMART_FORM}", timeout=5_000
        )
        for candidate in (
                await form.get_attribute("action") or "",
                await self.page.locator(f"xpath={self.X_SMART_CONT}//img").get_attribute("src")
                or "",
        ):
            m = re.search(r"key=([^_&/]+)", candidate)
            if m:
                return m.group(1)
        return None

    async def _grab_current_images(self) -> Tuple[bytes, bytes] | None:
        try:
            img_url = await self.page.get_attribute(
                f"xpath={self.X_SMART_CONT}//img", "src"
            )
            task_url = await self.page.get_attribute(
                'xpath=//img[contains(@class,"TaskImage")]', "src"
            )

            if not (img_url and task_url):
                return None

            img_b = requests.get(img_url, timeout=20).content
            task_b = requests.get(task_url, timeout=20).content
            return img_b, task_b
        except Exception as e:
            print(e)
            return None

    async def _solve_advanced(self) -> Tuple[Optional[bool], str]:
        if await self._detect_smart() or await self._detect_text():
            if self.solver == "capsola":
                return await self._via_capsola()
            else:
                return await self._via_2captcha()
        return None, "unknown captcha form"

    async def _via_capsola(self) -> Tuple[Optional[bool], str]:
        if not self.api_capsola:
            raise RuntimeError("Capsola API key missing")

        headers = {"Content-Type": "application/json", "X-API-Key": self.api_capsola}
        url_create, url_result = "https://api.capsola.cloud/create", "https://api.capsola.cloud/result"

        if await self._detect_smart():
            ok, payload = await self._prepare_capsola_smart()
        else:
            ok, payload = await self._prepare_capsola_text()
        if not ok:
            return False, payload  # payload содержит сообщение об ошибке

        try:
            resp = requests.post(url_create, json=payload, headers=headers, timeout=30).json()
        except requests.RequestException as e:
            return False, f"capsola create error: {e}"
        if resp.get("status") != 1:
            return False, f"capsola create returned error: {resp}"

        task_id = resp["response"]
        solution: str | None = None
        deadline = time.time() + 180
        while time.time() < deadline:
            await asyncio.sleep(5)
            try:
                res = requests.post(url_result, json={"id": task_id}, headers=headers, timeout=15).json()
            except requests.RequestException:
                continue
            if res.get("status") == 1:
                solution = res["response"]
                break
            if res.get("status") == 0 and res.get("response") != "CAPCHA_NOT_READY":
                return False, f"capsola error: {res}"
        if not solution:
            return False, "capsola timeout"

        return await self._apply_solution(solution)

    async def _prepare_capsola_smart(self) -> Tuple[bool, dict | str]:
        try:
            key = await self._extract_key()

            if key:
                img = requests.get(
                    f"https://ext.captcha.yandex.net/image?key={key}&data=img",
                    timeout=15,
                ).content
                task = requests.get(
                    f"https://ext.captcha.yandex.net/image?key={key}&data=task",
                    timeout=15,
                ).content
            else:
                grabbed = await self._grab_current_images()
                if not grabbed:
                    return False, "SmartCaptcha: images not found in DOM"
                img, task = grabbed

            return True, {
                "type": "SmartCaptcha",
                "click": base64.b64encode(img).decode(),
                "task": base64.b64encode(task).decode(),
            }
        except Exception as e:
            return False, f"SmartCaptcha download error: {e}"

    async def _prepare_capsola_text(self) -> Tuple[bool, dict | str]:
        try:
            img_url = await self.page.locator(f"xpath={self.X_CAPTCHA_IMG}").get_attribute("src")
            img_b = requests.get(img_url, timeout=15).content
            return True, {"type": "TextCaptcha", "task": base64.b64encode(img_b).decode()}
        except Exception as e:
            return False, f"TextCaptcha download error: {e}"

    async def _via_2captcha(self) -> Tuple[Optional[bool], str]:
        if not self.api_2captcha:
            raise RuntimeError("2captcha API key missing")

        return (
            await self._solve_smart_2captcha()
            if await self._detect_smart()
            else await self._solve_text_2captcha()
        )

    async def _solve_smart_2captcha(self) -> Tuple[Optional[bool], str]:
        try:
            key = await self._extract_key()
            if key:
                img_b = requests.get(
                    f"https://ext.captcha.yandex.net/image?key={key}&data=img",
                    timeout=15,
                ).content
                task_b = requests.get(
                    f"https://ext.captcha.yandex.net/image?key={key}&data=task",
                    timeout=15,
                ).content
            else:
                grabbed = await self._grab_current_images()
                if not grabbed:
                    return False, "SmartCaptcha: images not found in DOM"
                img_b, task_b = grabbed

            combo = self._merge_images(img_b, task_b)
            payload = {
                "key": self.api_2captcha,
                "method": "base64",
                "body": combo,
                "json": 1,
                "coordinatescaptcha": 1,
                "textinstructions": "Click the silhouettes",
            }
            resp = requests.post("https://2captcha.com/in.php", data=payload, timeout=30).json()
        except Exception as e:
            return False, f"in.php error: {e}"

        if resp.get("status") != 1:
            return False, f"in.php bad status: {resp}"

        sol = await self._poll_2captcha(resp["request"])
        return (await self._apply_solution(sol)) if sol else (False, "SmartCaptcha timeout")

    async def _solve_text_2captcha(self) -> Tuple[Optional[bool], str]:
        try:
            question = (await self.page.locator(f"xpath={self.X_TEXT_LABEL}").inner_text()).strip()
            payload = {
                "clientKey": self.api_2captcha,
                "languagePool": "rn",
                "task": {"type": "TextCaptchaTask", "comment": question},
            }
            resp = requests.post("https://api.2captcha.com/createTask", json=payload, timeout=30).json()
        except Exception as e:
            return False, f"createTask error: {e}"
        if resp.get("errorId", 1) != 0:
            return False, f"createTask returned error: {resp}"

        sol = await self._poll_2captcha_task(resp["taskId"])
        if sol is None:
            return False, "TextCaptcha timeout"

        return await self._apply_solution(sol)

    async def _poll_2captcha(self, cap_id: str) -> Optional[str]:
        deadline = time.time() + 120
        while time.time() < deadline:
            await asyncio.sleep(5)
            res = requests.get(
                "https://2captcha.com/res.php",
                params={
                    "key": self.api_2captcha,
                    "action": "get",
                    "id": cap_id,
                    "json": 1,
                },
                timeout=10,
            ).json()
            if res.get("status") == 1:
                return res["request"]
            if res.get("request") not in ("CAPCHA_NOT_READY",):
                break
        return None

    async def _poll_2captcha_task(self, task_id: int) -> Optional[str]:
        deadline = time.time() + 120
        while time.time() < deadline:
            await asyncio.sleep(5)
            res = requests.post(
                "https://api.2captcha.com/getTaskResult",
                json={"clientKey": self.api_2captcha, "taskId": task_id},
                timeout=10,
            ).json()
            if res.get("errorId", 1) != 0:
                return None
            if res.get("status") == "ready":
                return res["solution"]["text"]
        return None

    @staticmethod
    def _merge_images(img_b: bytes, task_b: bytes) -> str:
        img  = Image.open(io.BytesIO(img_b))
        task = Image.open(io.BytesIO(task_b))
        combo = Image.new("RGB", (max(img.width, task.width), img.height + task.height), "white")
        combo.paste(img, (0, 0))
        combo.paste(task, (0, img.height))
        buf = io.BytesIO()
        combo.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    async def _apply_solution(self, sol: Union[str, List[dict]]) -> Tuple[bool, str]:
        if await self._detect_smart():
            coords: List[Tuple[float, float]]
            if isinstance(sol, list):
                coords = [(float(c["x"]), float(c["y"])) for c in sol]
            else:
                coords = [(float(x), float(y)) for x, y in re.findall(r"x=([\d.]+),y=([\d.]+)", sol)]
            if not coords:
                return False, "bad coords format"

            try:
                img = await self.page.locator(f"xpath={self.X_SMART_CONT}//img").first.element_handle()
                box = await img.bounding_box()
                for x, y in coords:
                    await self.page.mouse.click(box["x"] + x, box["y"] + y)
                    await self.page.wait_for_timeout(150)
                await self.click(self.X_SUBMIT_BTN)
            except Exception as e:
                return False, f"click/submit error: {e}"
            return True, "Капча пройдена успешно"

        try:
            await self.page.locator(f"xpath={self.X_TEXT_INPUT}").fill(sol)
            await self.click(self.X_SUBMIT_BTN)
        except Exception as e:
            return False, f"submit error: {e}"
        return True, "Капча пройдена успешно"
