# Requirements Document

## Introduction

Ushbu hujjat Telegram "Lumberjack" (daraxt kesuvchi qahramon) o'yinini avtomatik tarzda o'ynaydigan Python bot (kompyuter ko'rish skripti) uchun talablarni belgilaydi. Brauzer xavfsizlik cheklovlari (CORS/iframe) sababli bot brauzer kodiga tegmaydi; uning o'rniga operatsion tizim va apparat darajasida ishlaydi, ya'ni ekran piksellarini tahlil qiladi va sichqoncha bosishlarini simulyatsiya qiladi.

Bot quyidagilarni bajaradi: daraxt tanasi atrofidagi piksel ranglarini kuzatib shoxlarni aniqlaydi, qahramonni xavfsiz tomonga o'tkazadi, har bir muvaffaqiyatli kesishni sanaydi va foydalanuvchi belgilagan maqsadli ballga (target_score) yetganda avtomatik to'xtaydi. Skript boshlashdan oldin kalibrlash imkonini beradi va boshqaruv tugmalari orqali ishga tushirish hamda favqulodda to'xtatish funksiyalarini taqdim etadi.

## Glossary

- **Bot**: Telegram "Lumberjack" o'yinini avtomatik o'ynaydigan Python skript tizimi.
- **Screen_Capture_Module**: Ekran piksellarini suratga oluvchi komponent (ImageGrab yoki OpenCV asosida).
- **Branch_Detector**: Daraxt tanasining chap va o'ng nuqtalaridagi piksel ranglarini tahlil qilib shoxlarni aniqlovchi komponent.
- **Click_Simulator**: Sichqoncha bosishlarini simulyatsiya qiluvchi komponent (pyautogui asosida).
- **Score_Counter**: Muvaffaqiyatli kesishlar sonini hisoblovchi komponent.
- **Calibration_Module**: O'yin oynasi (Canvas) ekran koordinatalarini sozlash imkonini beruvchi komponent.
- **Keyboard_Listener**: Klaviatura tugmalarini kuzatuvchi komponent (keyboard kutubxonasi asosida).
- **target_score**: Foydalanuvchi fayl boshida belgilaydigan maqsadli ball qiymati (masalan, 269).
- **Branch**: Daraxt tanasidan chiqib turgan shox; rangi jigarrang (brown) yoki barg-yashil (leaf-green) bo'ladi.
- **Hero**: O'yin qahramoni; daraxt tanasining chap yoki o'ng tomonida turadi.
- **Safe_Side**: Daraxt tanasining shox mavjud bo'lmagan tomoni.
- **Chop**: Bitta muvaffaqiyatli kesish harakati (bitta sichqoncha bosishi).

## Requirements

### Requirement 1: Kutubxona va muhit bog'liqliklari

**User Story:** Foydalanuvchi sifatida men botning kerakli kutubxonalar yordamida ishlashini xohlayman, shunda ekranni o'qish, sichqoncha bosish va to'xtatish imkoniyatlari mavjud bo'ladi.

#### Acceptance Criteria

1. THE Bot SHALL ekranni suratga olish uchun ImageGrab yoki OpenCV kutubxonalaridan kamida bittasi mavjud bo'lganidan foydalanadi.
2. THE Bot SHALL sichqoncha bosishlarini simulyatsiya qilish uchun pyautogui kutubxonasidan foydalanadi.
3. THE Bot SHALL klaviatura tugmalarini kuzatish uchun keyboard kutubxonasidan foydalanadi.
4. WHEN Bot ishga tushganda, THE Bot SHALL boshqa har qanday amalni bajarishdan oldin barcha talab qilingan kutubxonalar (ImageGrab yoki OpenCV, pyautogui va keyboard) o'rnatilganligini tekshiradi.
5. IF talab qilingan kutubxonalardan bir yoki bir nechtasi o'rnatilmagan bo'lsa, THEN THE Bot SHALL terminalga har bir yetishmayotgan kutubxonaning nomini va uni o'rnatish buyrug'ini ko'rsatadi.
6. IF talab qilingan kutubxonalardan kamida bittasi o'rnatilmagan bo'lsa, THEN THE Bot SHALL hech qanday ekranni suratga olish, sichqoncha bosish yoki klaviatura kuzatish amalini bajarmasdan ishni to'xtatadi.

### Requirement 2: Vizual tahlil va shox aniqlash

**User Story:** Foydalanuvchi sifatida men botning daraxt tanasi atrofidagi ranglarni kuzatib shoxlarni aniqlashini xohlayman, shunda qahramon shoxga urilmasdan xavfsiz tomonda turadi.

#### Acceptance Criteria

1. WHEN har bir kesish (Chop) tsikli boshlanadi, THE Branch_Detector SHALL daraxt tanasining chap va o'ng tomonidagi belgilangan piksel nuqtalarining rang qiymatlarini 100 millisekund ichida o'qiydi.
2. WHEN qahramon (Hero) turgan tomonda o'qilgan rang shox (Branch) rangiga sozlangan rang chegarasi (tolerance) doirasida mos kelsa, THE Bot SHALL qahramonni qarama-qarshi tomonga (Safe_Side) 100 millisekund ichida o'tkazadi.
3. IF qahramon turgan tomonda o'qilgan rang shox rangiga rang chegarasi doirasida mos kelmasa, THEN THE Bot SHALL qahramonni joriy tomonda qoldirib kesishni davom ettiradi.
4. THE Branch_Detector SHALL shox rangini aniqlashda foydalanuvchi tomonidan sozlanadigan, 0 dan 255 gacha bo'lgan butun son rang chegarasi (tolerance) qiymatidan foydalanadi; sozlanmagan holatda standart qiymat 30 bo'ladi.
5. IF chap va o'ng tomonlarning har ikkalasida ham shox rangi bir vaqtning o'zida aniqlansa, THEN THE Bot SHALL kesishni to'xtatadi, qahramonni joriy tomonda qoldiradi va foydalanuvchiga xavfli holatni bildiruvchi indikatsiya ko'rsatadi.
6. IF piksel rang qiymatlarini o'qib bo'lmasa, THEN THE Bot SHALL kesishni to'xtatadi va o'qish muvaffaqiyatsiz bo'lganini bildiruvchi xatolik indikatsiyasini ko'rsatadi.

### Requirement 3: Ball sanash va to'xtatish tizimi

**User Story:** Foydalanuvchi sifatida men botning kesishlarni sanab, belgilangan maqsadli ballga yetganda to'xtashini xohlayman, shunda o'yin kerakli ballda yakunlanadi.

#### Acceptance Criteria

1. THE Bot SHALL fayl boshida joylashgan sozlanadigan target_score o'zgaruvchisidan maqsadli ball qiymatini oladi, bu qiymat 1 dan 1 000 000 gacha bo'lgan butun son bo'lishi kerak.
2. IF target_score qiymati butun son bo'lmasa yoki 1 dan kichik yoki 1 000 000 dan katta bo'lsa, THEN THE Bot SHALL kesishni boshlamaydi va target_score qiymati yaroqsizligini bildiruvchi xatolik xabarini terminalga chop etadi.
3. WHEN bitta kesish muvaffaqiyatli bajarilsa, THE Score_Counter SHALL joriy ball hisobini bir birlikka oshiradi.
4. WHEN joriy ball hisobi bir birlikka oshsa, THE Bot SHALL yangilangan ball qiymatini terminalga chop etadi.
5. WHEN joriy ball hisobi target_score qiymatiga teng yoki undan katta bo'lsa, THE Bot SHALL yangi kesishni boshlamaydi, joriy kesish jarayonini to'xtatadi va dasturni yakunlaydi.

### Requirement 4: Kalibrlash rejimi

**User Story:** Foydalanuvchi sifatida men ishga tushirishda o'yin oynasi koordinatalarini sozlash imkonini xohlayman, shunda bot turli ekran o'lchamlari va oyna joylashuvlarida to'g'ri ishlaydi.

#### Acceptance Criteria

1. WHEN Bot ishga tushganda, THE Calibration_Module SHALL o'yin oynasi (Canvas) koordinatalarini (chap nuqta, o'ng nuqta, yuqori nuqta) sozlash uchun kalibrlash rejimini ishga tushiradi.
2. WHILE kalibrlash rejimi faol bo'lganda, THE Calibration_Module SHALL har bir koordinatani belgilash uchun tartiblangan, raqamlangan yozma ko'rsatmalarni terminalda taqdim etadi.
3. WHILE kalibrlash rejimi faol bo'lganda, THE Calibration_Module SHALL joriy sichqoncha koordinatalarini (X, Y piksellarda) kamida har 100 millisekundda terminalda yangilab ko'rsatadi.
4. THE Calibration_Module SHALL sozlangan koordinatalarni Branch_Detector va Click_Simulator tomonidan ishlatish uchun, ko'rsatish holatidan qat'i nazar, saqlaydi.
5. IF sozlangan koordinata qiymati 0 dan kichik bo'lsa yoki X uchun ekran kengligidan yoki Y uchun ekran balandligidan oshib ketsa, THEN THE Calibration_Module SHALL koordinatani rad etadi, terminalga xato xabarini ko'rsatadi va oldingi saqlangan koordinatani o'zgartirmasdan saqlab qoladi.
6. IF koordinatalarni saqlash amali muvaffaqiyatsiz bo'lsa, THEN THE Calibration_Module SHALL oldingi koordinatalarni o'zgartirmasdan saqlab qoladi, xatolik indikatsiyasini ko'rsatadi va joriy koordinatalarni terminalda ko'rsatishni davom ettiradi.

### Requirement 5: Xavfsizlik va ritm

**User Story:** Foydalanuvchi sifatida men kesishlar orasida tasodifiy kechikish bo'lishini xohlayman, shunda o'yin tezkor signallarni rad etmaydi va bot xatti-harakati inson tezligiga o'xshaydi.

#### Acceptance Criteria

1. WHEN ketma-ket ikki kesish bajarilsa, THE Click_Simulator SHALL ular orasida foydalanuvchi belgilagan minimal va maksimal qiymatlar oralig'ida bir tekis taqsimlangan tasodifiy kechikish qo'shadi.
2. THE Click_Simulator SHALL tasodifiy kechikish uchun foydalanuvchi sozlay oladigan minimal va maksimal qiymatlarni 10 millisekunddan 5000 millisekundgacha oraliqda qabul qiladi.
3. IF foydalanuvchi belgilagan minimal qiymat maksimal qiymatdan katta bo'lsa, yoki qiymatlardan biri 10–5000 millisekund oralig'idan tashqarida bo'lsa, THEN THE Click_Simulator SHALL kiritilgan qiymatlarni rad etadi, rad etilish sababini ko'rsatuvchi xatolik xabarini chiqaradi va oldingi amaldagi sozlamalarni o'zgartirmasdan saqlab qoladi.

### Requirement 6: Boshqaruv tugmalari

**User Story:** Foydalanuvchi sifatida men botni klaviatura tugmalari orqali boshqarishni xohlayman, shunda istalgan vaqtda ishga tushirishim va to'xtatishim mumkin.

#### Acceptance Criteria

1. WHILE Bot ishga tushgan va kutish holatida bo'lganda, WHEN foydalanuvchi 'S' tugmasini bossa, THE Bot SHALL kesish jarayonini 500 millisekund ichida boshlaydi.
2. WHILE Bot kesish jarayonida bo'lganda, WHEN foydalanuvchi 'Q' tugmasini bossa, THE Bot SHALL kesishni 1 soniya (1000 millisekund) ichida to'xtatadi va dasturni yakunlaydi.
3. THE Keyboard_Listener SHALL 'S' va 'Q' tugmalarini Bot ishlash davomida kamida har 100 millisekundda kuzatadi.
4. IF foydalanuvchi 'S' tugmasini Bot kutish holatida bo'lmagan paytda bossa, THEN THE Bot SHALL bu bosishni e'tiborsiz qoldiradi va joriy holatini o'zgartirmaydi.
5. WHEN dastur yakunlanish jarayoni boshlansa, THE Keyboard_Listener SHALL tugmalarni kuzatishni darhol to'xtatadi.

### Requirement 7: Hujjatlashtirish va ishga tushirish yo'riqnomasi

**User Story:** Foydalanuvchi sifatida men tayyor, izohlangan kod va ishga tushirish yo'riqnomasini xohlayman, shunda skriptni qiyinchiliksiz ishga tushira va kalibrlay olaman.

#### Acceptance Criteria

1. THE Bot SHALL har bir asosiy komponentni (Screen_Capture_Module, Branch_Detector, Click_Simulator, Score_Counter, Calibration_Module, Keyboard_Listener) izohlovchi sharhlarga ega bo'lgan, qo'shimcha tahrirsiz ishga tushiriladigan to'liq kod sifatida taqdim etiladi.
2. THE Bot SHALL foydalanuvchi sozlay oladigan o'zgaruvchilarni (target_score, koordinatalar, rang chegarasi va minimal/maksimal kechikish) izohlovchi sharhlarni kod ichida taqdim etadi.
3. THE Bot SHALL skriptni o'rnatish, ishga tushirish va boshlash bo'yicha tartiblangan, raqamlangan bosqichlarni o'z ichiga olgan yo'riqnomani taqdim etadi.
4. THE Bot SHALL koordinatalarni kalibrlash bo'yicha (chap, o'ng va yuqori nuqtalarni belgilash hamda saqlash) tartiblangan, raqamlangan bosqichlarni o'z ichiga olgan yo'riqnomani taqdim etadi.
