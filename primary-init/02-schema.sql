CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(160) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name VARCHAR(120) NOT NULL,
  role VARCHAR(16) NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
  id BIGSERIAL PRIMARY KEY,
  slug VARCHAR(140) UNIQUE NOT NULL,
  name VARCHAR(140) NOT NULL,
  summary VARCHAR(300) NOT NULL,
  description TEXT NOT NULL,
  price NUMERIC(12,2),
  image_url TEXT,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS survey_responses (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
  product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  intent VARCHAR(40) NOT NULL,
  comment TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS offices (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  address VARCHAR(240) NOT NULL,
  latitude NUMERIC(9,6) NOT NULL,
  longitude NUMERIC(9,6) NOT NULL,
  phone VARCHAR(40),
  email VARCHAR(160)
);

-- Бастапқы 3 бірегей өнім (Smart Campus экожүйесі)
INSERT INTO products (slug, name, summary, description, price, image_url, is_active) VALUES
(
  'smart-dorm-pass',
  'Smart Dormitory FaceID & QR Жүйесі',
  'Студенттік жатақханаларға қауіпсіз әрі жылдам кіруді қамтамасыз ететін биометриялық өткізу пункті.',
  'Smart Dormitory жүйесі университет жатақханаларындағы қауіпсіздік деңгейін жаңа сатыға көтереді. Дәстүрлі қағаз рұқсатнамалар мен магниттік карталардың орнына бет-әлпетті тану (FaceID) және динамикалық QR-код технологиясы қолданылады. Бұл бөгде тұлғалардың ғимаратқа кіруіне толық тосқауыл қояды.\n\nМақсатты аудитория: Жоғары оқу орындарының әкімшілігі, жатақхана коменданттары және студенттер. Ерекшеліктері: тәулік бойы автоматты бақылау, ата-аналарға хабарлама жіберу модулі, турникеттермен жылдам интеграция. Ұсыну моделі: Ай сайынғы бұлттық жазылым немесе бір реттік орнату лицензиясы.',
  150000.00,
  'https://images.unsplash.com/photo-1555421689-491a97ff2040?auto=format&fit=crop&w=800&q=80',
  true
),
(
  'campus-ai-tutor',
  'Campus AI-Тьютор Көмекшісі',
  'Студенттердің оқу үлгерімін талдап, жеке оқу жоспарын құрастыратын жасанды интеллект платформасы.',
  'Campus AI-Тьютор — әрбір студенттің пәндер бойынша білім деңгейін үздіксіз бақылайтын интеллектуалды көмекші. Жүйе емтихандарға дайындық кезінде әлсіз тұстарды анықтап, университеттің электронды кітапханасынан нақты дәрістер мен әдебиеттерді ұсынады.\n\nМақсатты аудитория: Бакалавриат және магистратура студенттері, оқытушылар құрамы. Ерекшеліктері: 24/7 қазақ және орыс тілдерінде кеңес беру, LMS жүйелерімен (Moodle, Platonus) толық үйлесімділік, үлгерім аналитикасы. Ұсыну моделі: Бір студентке шаққандағы жылдық академиялық лицензия.',
  45000.00,
  'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=800&q=80',
  true
),
(
  'e-dean-queue',
  'Электронды Деканат және Кезек',
  'Анықтамалар мен академиялық өтініштерді онлайн рәсімдеуге арналған цифрлық қызмет көрсету орталығы.',
  'Электронды Деканат студенттерді ұзын-сонар кезекте тұрудан босатады. Оқу орнынан анықтама алу, жатақханаға өтініш беру немесе академиялық демалыс рәсімдеу енді смартфон арқылы 3 минут ішінде орындалады. Барлық құжаттар электронды цифрлық қолтаңбамен (ЭЦҚ) расталады.\n\nМақсатты аудитория: Университет деканаттары, тіркеу кеңсесі (Office of the Registrar) және студенттер. Ерекшеліктері: Telegram-бот арқылы кезекті брондау, құжат мәртебесін нақты уақытта бақылау, қағаз шығынын 90%-ға азайту. Ұсыну моделі: Толық модульдік орнату және техникалық қолдау.',
  95000.00,
  'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=800&q=80',
  true
) ON CONFLICT (slug) DO NOTHING;

-- Бастапқы кеңсе (Астана қаласының ашық координаттары)
INSERT INTO offices (name, address, latitude, longitude, phone, email) VALUES
(
  'Smart Campus Бас Кеңсесі (Астана)',
  'Астана қ., Мәңгілік Ел даңғылы, 55/11 (EXPO IT-квартал)',
  51.089100,
  71.416800,
  '+7 (7172) 55-01-99',
  'info@smartcampus.kz'
);