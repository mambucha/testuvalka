# Розгортання на Oracle Cloud (безкоштовно, без засинання) — покроково

Ця інструкція розрахована на людину, яка раніше серверів не налаштовувала.
Читай згори вниз, копіюй команди по одній. Усе, що починається з `sudo`, —
виконується на сервері (у вікні SSH). Команди без `sudo` на початку розділу 1 —
на твоєму комп'ютері (Windows, у PowerShell).

Підсумок того, що будуємо: одна безкоштовна віртуальна машина Oracle, на ній у
Docker працюють три речі — наш застосунок, база даних PostgreSQL і проксі Caddy
(він робить https). Машина працює цілодобово, **не засинає**, тож посилання на
тест доступне завжди.

---

## Крок 1. Покласти проєкт на GitHub (на своєму комп'ютері)

Щоб потім легко оновлювати. У PowerShell, у теці проєкту `E:\Projects\Testuvalka`:

```powershell
git init
git add .
git commit -m "Testuvalka"
```

Далі створи репозиторій на https://github.com (кнопка New). Роби його
**публічним** — так простіше (клон на сервер без паролів) і безпечно: секрети
(`.env`) у git не потрапляють, а числа задач залежать від `TESTUVALKA_SECRET`,
якого в репозиторії немає. GitHub покаже команди «…or push an existing
repository»; виконай їх, приблизно так:

```powershell
git remote add origin https://github.com/ТВІЙ_ЛОГІН/testuvalka.git
git branch -M main
git push -u origin main
```

> Файл `.env` і файли `*.db` у git не потраплять — так і має бути (вони в
> `.gitignore`). Секрети живуть лише на сервері.

---

## Крок 2. Створити акаунт Oracle Cloud

1. https://www.oracle.com/cloud/free → **Start for free**.
2. Знадобиться картка для перевірки (Always Free **не списує** гроші).
3. **Home Region** обери **Germany Central (Frankfurt)** — його потім не змінити,
   і саме до нього прив'язані безкоштовні ресурси. Франкфурт — ЄС, близько й
   зазвичай має вільні потужності.

---

## Крок 3. Створити віртуальну машину (ARM, Always Free)

1. Меню ☰ → **Compute** → **Instances** → **Create instance**.
2. Ім'я: `testuvalka`.
3. **Image and shape** → **Edit**:
   - Image: **Canonical Ubuntu 24.04**.
   - Shape → **Ampere** → `VM.Standard.A1.Flex`, постав **2 OCPU / 12 GB**
     (це в межах безкоштовного; вистачить із запасом).
4. **Add SSH keys**: на своєму комп'ютері в PowerShell створи ключ (Enter на всі
   запитання):
   ```powershell
   ssh-keygen -t ed25519
   ```
   Потім покажи відкритий ключ і скопіюй увесь рядок:
   ```powershell
   Get-Content $HOME\.ssh\id_ed25519.pub
   ```
   В Oracle вибери **Paste public keys** і встав його.
5. Переконайся, що призначається **публічна IPv4-адреса** (за замовчуванням так).
6. **Create**. За ~1–2 хв машина запуститься. Запиши її **Public IP address**
   (далі позначаю як `IP`).

---

## Крок 4. Відкрити порти в хмарному фаєрволі Oracle

За замовчуванням відкритий лише SSH (22). Треба відкрити 80 і 443 (веб).

1. На сторінці інстансу → блок **Primary VNIC** → клікни на **Subnet**.
2. Відкрий **Security List** (Default Security List).
3. **Add Ingress Rules** — додай два правила:
   - Source `0.0.0.0/0`, IP Protocol **TCP**, Destination Port **80**.
   - Source `0.0.0.0/0`, IP Protocol **TCP**, Destination Port **443**.
4. Зберегти.

---

## Крок 5. Підключитися до сервера (SSH)

На своєму комп'ютері в PowerShell (підстав свій `IP`):

```powershell
ssh ubuntu@IP
```

Перший раз спитає «Are you sure…?» — введи `yes`. Ти в терміналі сервера.

---

## Крок 6. ВАЖЛИВО: відкрити порти всередині самої машини

⚠️ Це головна пастка Oracle: **окрім хмарного фаєрвола, всередині Ubuntu теж є
свій фаєрвол**, який блокує 80/443. Без цього кроку сайт «не відкривається», хоч
усе інше правильно. Виконай на сервері:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo apt-get update && sudo apt-get install -y netfilter-persistent
sudo netfilter-persistent save
```

(Порт 22/SSH уже дозволений — його не чіпаємо.)

---

## Крок 7. Встановити Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
```

Щоб зміна групи подіяла — вийди і зайди знову:

```bash
exit
```
```powershell
ssh ubuntu@IP
```

Перевірка (має показати версію, без `sudo`):

```bash
docker version
```

---

## Крок 8. Безкоштовний домен (для https)

Для https потрібне ім'я домену (на «голий» IP сертифікат не видають). Найпростіше —
безкоштовний субдомен на https://www.duckdns.org:

1. Увійди (Google/GitHub).
2. Придумай ім'я, напр. `testuvalka` → отримаєш `testuvalka.duckdns.org`.
3. У поле **current ip** впиши свій `IP` і натисни **update ip**.

Далі домен = `testuvalka.duckdns.org`. (Якщо маєш власний домен — просто зроби
A-запис на `IP`.)

> Не хочеш домену взагалі? Тоді працюватимеш по http:// за IP — див. коментар у
> файлі `Caddyfile` (треба розкоментувати блок `:80`). Але https краще.

---

## Крок 9. Завантажити проєкт на сервер

```bash
sudo apt-get install -y git
git clone https://github.com/ТВІЙ_ЛОГІН/testuvalka.git
cd testuvalka
```

(Публічний репозиторій клонується без пароля. Якщо ти зробив його приватним —
GitHub попросить логін і **токен** замість пароля: Settings → Developer settings
→ Personal access tokens.)

---

## Крок 10. Створити файл секретів `.env`

Згенеруй два довгі випадкові рядки:

```bash
openssl rand -hex 32   # це буде TESTUVALKA_SECRET
openssl rand -hex 32   # це буде TESTUVALKA_TEACHER_TOKEN
openssl rand -hex 16   # це буде DB_PASSWORD
```

Створи файл `.env` (редактор nano):

```bash
nano .env
```

Встав такий вміст, підставивши свої значення (домен — свій):

```
DOMAIN=testuvalka.duckdns.org
TESTUVALKA_SECRET=встав_перший_рядок
TESTUVALKA_TEACHER_TOKEN=встав_другий_рядок
DB_PASSWORD=встав_третій_рядок
```

Збережи: `Ctrl+O`, `Enter`, потім `Ctrl+X`.

> ⚠️ `TESTUVALKA_SECRET` **не можна змінювати** після старту семестру — від нього
> залежать усі числа в задачах. Запиши його собі окремо в надійне місце.
> `TESTUVALKA_TEACHER_TOKEN` — це твій пароль до журналу оцінок.

---

## Крок 11. Запустити

```bash
docker compose up -d --build
```

Перший раз збирається кілька хвилин. Перевір, що всі три сервіси піднялись:

```bash
docker compose ps
```

Логи (якщо цікаво / щось не так):

```bash
docker compose logs -f app
```

(вийти з логів — `Ctrl+C`)

---

## Крок 12. Перевірити

У браузері відкрий:

- Тест для студента: `https://testuvalka.duckdns.org/?test=lecture1`
- Кабінет викладача: `https://testuvalka.duckdns.org/teacher.html`

Перший запуск застосунку сам створить таблиці й завантажить тести з `tests.yaml`
(бо в compose стоїть `TESTUVALKA_AUTOLOAD: tests.yaml`).

Посилання студентам — це просто адреса тесту з потрібним ключем, напр.
`https://testuvalka.duckdns.org/?test=lecture1`. Вона працює цілодобово.

---

## Крок 13. Як ДОДАВАТИ / МІНЯТИ тести пізніше

1. На своєму комп'ютері зміни `tests.yaml` (новий тест) і, якщо треба, додай
   шаблон задачі у `app/bank/…` (це вже код).
2. Заливай зміни:
   ```powershell
   git add . ; git commit -m "нові тести" ; git push
   ```
3. На сервері онови й перезапусти:
   ```bash
   cd ~/testuvalka
   git pull
   docker compose up -d --build
   ```

Тести оновляться автоматично на старті (за ключем; наявні спроби студентів не
чіпаються). Новий тест на **наявних** шаблонах — це лише кілька рядків у
`tests.yaml`. Новий **тип задачі** — це код (тому й потрібен `git push` + перезбір).

---

## Крок 14. Як забрати ОЦІНКИ

Відкрий `https://testuvalka.duckdns.org/teacher.html`, введи ключ тесту (напр.
`lecture1`) і свій `TESTUVALKA_TEACHER_TOKEN` → побачиш журнал і кнопку
**«Завантажити CSV (журнал)»** (Excel відкриє з кирилицею коректно). Там же —
сигнали аномалій (вставки, перемикання вкладки) як підказка, не як вирок.

---

## Дрібниці, які варто знати

- **Перезавантаження сервера.** Docker налаштований на автозапуск, а сервіси —
  `restart: unless-stopped`, тож після ребуту все підніметься само.
- **Дані в безпеці.** База лежить у Docker-томі `dbdata` і переживає і перезбір
  (`up --build`), і перезавантаження машини.
- **Резервна копія оцінок** (за бажанням, час від часу):
  ```bash
  cd ~/testuvalka
  docker compose exec -T db pg_dump -U testuvalka testuvalka > backup_$(date +%F).sql
  ```
- **Сайт не відкривається?** У 9 з 10 випадків це Крок 6 (внутрішній фаєрвол) або
  Крок 4 (хмарні правила). Перевір, що зробив обидва. Також дай Caddy ~30 с на
  перший сертифікат і перевір `docker compose logs caddy`.
- **DuckDNS і зміна IP.** Публічний IP Oracle-інстансу стабільний; якщо колись
  зміниться — просто онови його на duckdns.org.
