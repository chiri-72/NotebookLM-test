import json
import time
from pathlib import Path
import os

def import_provided_cookies(cookie_string):
    # Parse cookie string into dict
    cookies = {}
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            name, value = item.split('=', 1)
            cookies[name] = value

    # Create auth_data
    auth_data = {
        "cookies": cookies,
        "csrf_token": "", # Will be auto-extracted by client
        "session_id": "", # Will be auto-extracted by client
        "extracted_at": time.time()
    }

    cache_dir = Path.home() / ".notebooklm-mcp"
    cache_dir.mkdir(exist_ok=True)
    cache_path = cache_dir / "auth.json"

    with open(cache_path, "w") as f:
        json.dump(auth_data, f, indent=2)

    print(f"✅ 인증 정보 저장 완료: {cache_path}")
    print(f"파싱된 쿠키 개수: {len(cookies)}개")

if __name__ == "__main__":
    # The cookie string provided by the user
    raw_cookies = "__Secure-BUCKET=CBs; SID=g.a0006QiCidwCFpvjbS8Qyym7397deDxDtkjr2kOD-SzJ3cwfiULkO-a8iLgle-bbtBbaYSQBrwACgYKAfkSARISFQHGX2MiCrXVBcE3HMaIhJrQetKlvxoVAUF8yKqA7Ht5JT4sBiiTwfK_aFzr0076; __Secure-1PSID=g.a0006QiCidwCFpvjbS8Qyym7397deDxDtkjr2kOD-SzJ3cwfiULkaZPkEK5q7n0zOpXDk6BV-AACgYKARQSARISFQHGX2Mi86KxeDNpwjsMWOyYGduLHxoVAUF8yKpg6kXd4wo2iiAyw0MqsHtu0076; __Secure-3PSID=g.a0006QiCidwCFpvjbS8Qyym7397deDxDtkjr2kOD-SzJ3cwfiULkISUizI6rtYuQgavmhYJ_2QACgYKAfQSARISFQHGX2Mi2DWdmuQPse0Y3TIy2Lev7hoVAUF8yKrsA_V2pYVRDvMBgsDRlW310076; HSID=AT1MIKdYpev_PYBlx; SSID=A-0Kz-ix3Lv2yEdRd; APISID=s33b4fYJNUgso3WI/AeyZxGRbcO2wHJ7ob; SAPISID=2dvIHuWYwG7F1gPa/As1gwo7WfquwRVOXy; __Secure-1PAPISID=2dvIHuWYwG7F1gPa/As1gwo7WfquwRVOXy; __Secure-3PAPISID=2dvIHuWYwG7F1gPa/As1gwo7WfquwRVOXy; S=billing-ui-v3=9CJWvk70gjNLSJngd5y1mEGpVYR99y9vlIin7AvTwho:billing-ui-v3-efe=9CJWvk70gjNLSJngd5y1mEGpVYR99y9vlIin7AvTwho; OSID=g.a0006wiCiQAKx9sHOPqhh-1dwewxgzWeTTK-h7V96-CTw3B89BenOF1plz0KMA4YEDdWoSuoDwACgYKAYISARISFQHGX2Mihy7P6tReRsZ9jVjXX2QkPhoVAUF8yKoePMZM0P4M7lPewfZ5bl3E0076; __Secure-OSID=g.a0006wiCiQAKx9sHOPqhh-1dwewxgzWeTTK-h7V96-CTw3B89BenRSIOYUdQIvs_QHu5qLGROAACgYKAbYSARISFQHGX2MiNGi_Io7aKVDf74b0hD2UhxoVAUF8yKopn9SqHcrfXk-2dCAhWZjI0076; _gcl_au=1.1.90043713.1771316533; _ga=GA1.1.1409562753.1771316533; AEC=AaJma5sPP7c9FvqfJi618uTypoqRs8mNgQHeBdJCdqGMemauib7XuBpLUQ; NID=529=aNe7Cm_BPk6cHoVGRfwlfYx0SiruO-wicP_-0ZVJzKDvTT1K7sGySy5O281-hUeamDnfOIiLjG_Xo9NesUdZ3Zy4wuwGZzKCaKQLIfhXygPiNtBLMK1wYX-f1apLjMdljMIDB-0jIwmpnsDPvEHNU6lURPQC_ftubtHumN0QoLrdUGpwvDkNIFN5z6ObVY0iLkef-aGNF9zx6Czco-Yut8ArMJqz8xzMkPs9s9F9Pi3uFARL_NifrNvY3M5nYUvKr2RB7rMU83lVS47rjvac_NGfNYtA_YcMuCsaAXAyW1cfqaw3B9e6ugyUHpivLlnrm_n-Zxwzk5oCF5LYnV-SUmCdkXcSUTWO4Pp8NS6P-sH6Z0xlWS1N8NJf6t0v-XiMLXCwDGn3LdMowHiZrFsliA8KWuX_nHVso6Le09KI3eZpINbvMcrfWoVG3kqbFTJp0Jjsy88t_IIamJDxm7L2jyigg8naqPnzpBS1NOYzaSHQM8oHmsXxEy2l9AF93HJ3lV63cEoxMa-ob-lMKA-amJMGnS27f4AYSFq1_Xqlt3PleQQU1GBJ2W6niJDAWQwiWoDt7bSUYPO_ekhkbgLQmZJU5RItZsrkqhsLIBmgHcANCCVrL-FYgYKSvfNuDl5vuIWw73TgMwK2bzrfKvAx-9U_8TIE1eumNNOll-Fld2ooop2bGa1FIKeupcWElRWIVLJpUpsdy-W_QkhgTbCfrgBbjzrlisStur6LjGpv1MOphOWanMFdd1I_6qOhaCQg0qRgzQvEz69X6Ew_qauVsy2rlYfam_yXGMPcc3udcpfoWPFtHhembk-qdGJMtjCZxvnNE7cgc3IXjGev_WOmQvo4_yXj6BDqtwibA4gF9g8MjZS79KpzaqFo3-_cKJflebrQb4svJ455JmNZ4VtyABwlrlx1byRyAPZkKUTd3I7sDfW1tta_0x9BTDSEzlb4kUKjJcEqwScP4CZlHyYTlhH7y-UczVFVQjPuPb_mVwyx63rSx2tL-vtgHLu8b501c_sl82EouVgUMPWZybjFoATCHIntLaN1s1TVvStu1tKlTnOSqMJMa4t6oKqS_vKQkGtloFBit3FaudrG4fwniPz5cD7AunnUIfEmBurqKQxtBtuR4rRlsJqBssA286nESWAKPDcbCTM9a7VTYCtDUPT8NwfxjX1nPYOy34HcA6b0naQYl6pcfnWxrjdRhzQxem5MtUniL3HQ79T7hZeglKQofn5AG4V-XdTmoqNTo6sLn5tPKTtdN-q_GdKVvZDOY_8fOBUTgNYiW9vYUgjKb2oeiF-aKZZhRM85Mgqm0bXMW9_TMJy1C1ulZzGc8-IQzsrEcTgbdZizc_d1QhQg8pvTmw2UorMaIZL5D9KIOMGcnMa-AP5OoMEOw1Pir7nQgFY-o-18ChyUaIm6lDLLx4Kf1CjL; __Secure-1PSIDTS=sidts-CjIBBj1CYgH0IS_wxipQg3qlPuN-KM5WTMJueUUj9aAFix9lD4aVawB7QRmgw82V_gdHQxAA; __Secure-3PSIDTS=sidts-CjIBBj1CYgH0IS_wxipQg3qlPuN-KM5WTMJueUUj9aAFix9lD4aVawB7QRmgw82V_gdHQxAA; SIDCC=AKEyXzWPyVRitaRIWNyRm0sxHWh50MBEt3vpUVmcpxq86CrrkD7sE38MXtTiK2-btxinzz0NQAz5; __Secure-1PSIDCC=AKEyXzWakH40zNoxHYd6MH1Eyb8bryWHWoqhrGay6xnCJjVCWZe7967_6IZIAL91fj2J9iL3xYujJw; __Secure-3PSIDCC=AKEyXzWpxXHX6VR8X7l117cQypUiHYcDuV5O2Zqv5g6vdmYCFZDidajXenpo1v4X_UOXk-gam_-pFA; _ga_W0LDH41ZCB=GS2.1.s1771336279$o4$g1$t1771339334$j4$l0$h0"
    import_provided_cookies(raw_cookies)
