// Единый node-набор кейсов redact (queue-2/15): матрица форматов, утверждённая
// оператором, — позитивы (маскируется) и негативы (проходит). Прогоняется по
// всем копиям redact в workflow-файлах; копии обязаны быть байт-в-байт
// идентичны. Запуск: node tests/redact_matrix.mjs (из pytest —
// tests/test_redact_matrix.py). Сценарий извлекает функцию из живых файлов:
// рассинхрон копий или регресс паттерна ломает прогон.
// Критерий позитива двоякий (урок гейта 15: out!==input маскирует частичную
// замену): строка изменилась И секретный фрагмент (4-й элемент, если задан)
// не встречается в выводе.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const COPIES = [
  "skills/ship/reviewer.workflow.ts",
  "skills/ship/confirm.workflow.ts",
  "skills/code-review/code-review.workflow.ts",
  "skills/architecture/architecture.workflow.ts",
];

function extractRedact(rel) {
  const src = readFileSync(join(ROOT, rel), "utf8");
  const m = src.match(/function redact\(s: string\): string \{[\s\S]*?\n\}/);
  if (!m) throw new Error(`${rel}: function redact не найдена`);
  return m[0].replace("function redact(s: string): string {", "function redact(s) {");
}

// [маскировать, имя, вход, секретКоторогоНеДолжноБытьВВыводе?]
const CASES = [
  [true, "PEM PGP PRIVATE KEY BLOCK", "-----BEGIN PGP PRIVATE KEY BLOCK-----\nFAKEpgpbody\n-----END PGP PRIVATE KEY BLOCK-----", "FAKEpgpbody"],
  [true, "PEM цифры в префиксе", "-----BEGIN GO TC36 WMAP PRIVATE KEY-----\nFAKEdigitbody\n-----END GO TC36 WMAP PRIVATE KEY-----", "FAKEdigitbody"],
  [true, "PEM не-ASCII заголовок", "-----BEGIN ЗАКРЫТЫЙ КЛЮЧ RSA-----\nFAKEnonasciibody\n-----END ЗАКРЫТЫЙ КЛЮЧ RSA-----", "FAKEnonasciibody"],
  [true, "PEM CERTIFICATE (вердикт: маскируем)", "-----BEGIN CERTIFICATE-----\nFAKEcertbody\n-----END CERTIFICATE-----", "FAKEcertbody"],
  [true, "PEM TRUSTED CERTIFICATE", "-----BEGIN TRUSTED CERTIFICATE-----\nFAKetrustbody\n-----END TRUSTED CERTIFICATE-----", "FAKetrustbody"],
  [true, "PEM PUBLIC KEY", "-----BEGIN PUBLIC KEY-----\nFAKEpubbody\n-----END PUBLIC KEY-----", "FAKEpubbody"],
  [true, "PEM RSA (регресс-контроль)", "-----BEGIN RSA PRIVATE KEY-----\nFAKersabody\n-----END RSA PRIVATE KEY-----", "FAKersabody"],
  [true, "url user:pass@host", "https://user:FAKEs3cret@host.example/", "FAKEs3cret"],
  [true, "пароль в кавычках", 'password = "FAKEhunter2body"', "FAKEhunter2body"],
  [true, "token без кавычек", "token=FAKEabcdef123456", "FAKEabcdef123456"],
  [true, "api_key двоеточием", "api_key: FAKEsupersecret99", "FAKEsupersecret99"],
  [true, "access_token префиксный", "access_token=FAKEabc123def456", "FAKEabc123def456"],
  [true, "jwt значение (словарь 15)", "jwt: FAKEJWTVALUE123456", "FAKEJWTVALUE123456"],
  [true, "bearer-литерал", "Authorization: Bearer FAKEabc123-def456=", "FAKEabc123-def456="],
  [true, "basic-литерал", "basic RkFLRXVzZXI6RkFLRXBhc3N3b3Jk", "RkFLRXVzZXI6RkFLRXBhc3N3b3Jk"],
  [true, "Authorization: Basic (гейт 15: bearer до key=value)", "Authorization: Basic RkFLRXVzZXI6RkFLRXBhc3N3b3Jk", "RkFLRXVzZXI6RkFLRXBhc3N3b3Jk"],
  [true, "JWS из трёх сегментов целиком", "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.FAKESflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c", "FAKESflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"],
  [true, "Bearer + JWS (гейт 15: eyJ до bearer)", "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.FAKESflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c", "FAKESflKxw"],
  [true, "Bearer + двухсегментный токен (гейт 15)", "Bearer eyJhbGciOiJub25lIn0.eyJkYXRhIjoxfQ", "eyJkYXRhIjoxfQ"],
  [true, "JWS с padding === (гейт 15)", "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.FAKEL5EwMgBkRbFMR91mBPm4vOqQkx-3X0bGgVZj5J3gH6qL5E===", "L5E==="],
  [true, "JWS с raw base64 +/ в сегменте (гейт 15)", "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.FAKEwMg+BbFMR91mBPm4vOqQkx/3X0bGgVZj5J3gH6qL5E", "BbFMR91"],
  [true, "JWE из пяти сегментов", "eyJhbGci.eyJkYXRh.eyJpdiBl.eyJzaXJ0.eyJ0YWc", "eyJzaXJ0"],
  [true, "eyJ со словарным контекстом", "token=eyJyb290X2NhbGxiYWNrX3BhdGhfMQ", "eyJyb290X2NhbGxiYWNrX3BhdGhfMQ"],
  [true, "vendor sk-", "sk-FAKEa1b2c3d4e5f6", "FAKEa1b2c3d4e5f6"],
  [true, "vendor ghp_", "ghp_FAKEa1B2c3D4e5F6g7H8", "FAKEa1B2c3D4e5F6g7H8"],
  [true, "vendor AKIA", "AKIAFAKEIOSFODNN7", "FAKEIOSFODNN7"],
  [true, "JSON-ключ в кавычках", '"api_key": "FAKEv1.abc123def456"', "FAKEv1.abc123def456"],
  [true, "FP по замыслу: bare-key с прозой ≥4 символов (гейт 15)", "заголовок auth: подробнее в документации"],
  [false, "state=eyJ — не секрет (вердикт 15)", "state=eyJyb290X2NhbGxiYWNrX3BhdGhfMQ"],
  [false, "заголовок JWT в прозе без сигнатуры", "заголовок eyJhbGciOiJIUzI1NiJ9 декодируется в alg"],
  [false, "bearer-проза (урок 13)", "используем bearer authentication для запроса"],
  [false, "markdown-разделитель", "---\n\nтекст\n\n---"],
  [false, "BEGIN без END не маскируется", "упоминание -----BEGIN PRIVATE KEY----- без конца"],
  [false, "exclusion auth_type", "auth_type: bearer"],
  [false, "exclusion password_reset_url", 'password_reset_url: "https://x/reset"'],
  [false, "exclusion secret_name", "secret_name: my-tls-cert"],
  [false, "exclusion token_ttl (новый 15)", "token_ttl: 3600"],
  [false, "exclusion password_policy (новый 15)", "password_policy: strict"],
  [false, "exclusion auth_timeout (новый 15)", "auth_timeout: 30s"],
  [false, "exclusion secret_length (новый 15)", "secret_length: 32"],
  [false, "raw hex — хэш коммита (пропуск 15)", "коммит 5f4dcc3b5aa765d61d8327deb882cf99 исправляет баг"],
  [false, "query-креды с несловарным именем (пропуск 15)", "GET /api?state=abc123def456&next=/home"],
  [false, "значение короче 4 символов (пропуск 15)", "TOKEN=abc"],
  [false, "authorization в прозе (короткое значение)", "заголовок authorization: см. документацию"],
];

const bodies = COPIES.map(extractRedact);
let failed = 0;
for (let i = 1; i < bodies.length; i++) {
  if (bodies[i] !== bodies[0]) {
    console.error(`РАССИНХРОН: ${COPIES[i]} отличается от ${COPIES[0]}`);
    failed++;
  }
}
if (failed > 0) process.exit(1);

// eslint-disable-next-line no-new-func -- функция извлечена из доверенного файла этого же репо
const redact = new Function(`${bodies[0]}\nreturn redact;`)();

for (const [shouldMask, name, input, secret] of CASES) {
  const out = redact(input);
  const masked = out !== input;
  if (masked !== shouldMask) {
    console.error(`FAIL [${shouldMask ? "маскировать" : "пропускать"}] ${name} => ${JSON.stringify(out.slice(0, 120))}`);
    failed++;
    continue;
  }
  if (shouldMask && secret && out.includes(secret)) {
    // Частичное маскирование (урок гейта 15: «Bearer [REDACTED].payload» зелёный
    // по out!==input, но секрет открыт) — положительный кейс обязан убрать секрет.
    console.error(`УТЕЧКА ${name}: секрет ${JSON.stringify(secret.slice(0, 40))} остался в выводе`);
    failed++;
  }
  const again = redact(out);
  if (again !== out) {
    console.error(`НЕ ИДЕМПОТЕНТНО: ${name}`);
    failed++;
  }
}
console.log(`${COPIES.length} копии идентичны; кейсов: ${CASES.length}, упало: ${failed}`);
process.exit(failed === 0 ? 0 : 1);
