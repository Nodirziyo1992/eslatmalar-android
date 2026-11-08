# ESLATMALAR — Android `.apk` faylini olish

**Muallif:** Mingqulova Rayhona  
**Ilova:** Eslatmalar, Python/Kivy + SQLite

## Birinchi usul — GitHub Actions (Android SDK o‘rnatish shart emas)

1. GitHub hisobingizga kiring va **New repository** orqali masalan `eslatmalar-android` nomli repozitoriy yarating.
2. Bu ZIP arxivni to‘liq oching. **Yashirin `.github` papkasi ham** ichida ekanini tekshiring.
3. Arxiv ichidagi **barcha fayllarni** yangi repozitoriyga yuklang (`Add file` → `Upload files`), shuningdek `.github/workflows/build-apk.yml` ham yuklanganini tekshiring. GitHub brauzeri yashirin papkani qabul qilmasa, Git yoki GitHub Desktop orqali repozitoriyga nusxalang.
4. GitHub’da **Actions** → **Android APK — Eslatmalar** → **Run workflow** ni bosing.
5. Muvaffaqiyatli build tugaganidan keyin ishga tushirish sahifasidagi **Artifacts** dan `Eslatmalar-Mingqulova-Rayhona-Android-APK` arxivini yuklab oling.
6. Olingan arxivni oching. Ichida haqiqiy `.apk` fayli bo‘ladi. APK'ni Android telefoningizga ko‘chiring va qurilma ruxsat bersa o‘rnating.

**Eslatma:** Build uchun internet va GitHub Actions ishga tushishi zarur. Birinchi build SDK/NDK va boshqa komponentlarni yuklaydi. GitHub Actions build muvaffaqiyati ushbu muhitda tekshirilmagan; xato chiqsa, Actions logidagi aniq xatoni yuboring.

**Dastur maxfiyligi:** Tayyorlangan APK'ning barcha qaydlari telefoningizning ilova xotirasida saqlanadi, bulutga avtomatik yuklanmaydi.

## Ikkinchi usul — Ubuntu yoki WSL2 orqali

Ubuntu 22.04 yoki 24.04, Java 17, Python 3.10/3.11, Buildozer, Android SDK/NDK va talab etiladigan native kutubxonalar kerak.

1. Rasmiy ko‘rsatma: https://github.com/kivy/buildozer/blob/master/docs/source/installation.rst
2. Bu loyiha papkasida quyidagini ishga tushiring:

```bash
python3 -m pip install 'buildozer>=1.5' 'cython==0.29.34'
buildozer android debug
```

3. Yaratilgan APK `bin/` papkasida bo‘ladi.

## Tekshirilgan va tekshirilmagan holatlar

- `main.py` va `storage.py` Python sintaksis tekshiruvidan o‘tgan.
- SQLite ma’lumotlar qatlami: **23/23 test muvaffaqiyatli**.
- Kivy interfeysi Android telefonida tekshirilmagan.
- Ushbu arxiv **APK emas**, APK yaratish uchun to‘liq dastur kodi va avtomatik yig‘ish sozlamasidir.
