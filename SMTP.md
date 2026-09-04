# Как в Tesis сделана отправка почты (SMTP)

Коротко: один сервис на Nodemailer, внешний SMTP-провайдер по 465/587,
локально вся почта перехватывается Mailpit. Никакой очереди для писем нет —
письма отправляются прямо из бизнес-логики и намеренно не блокируют её.

## 1. Что где лежит

```
backend/src/mail/
├── mail.module.ts     # provider + export MailService
└── mail.service.ts    # весь SMTP: транспорт и все шаблоны писем
```

Модуль максимально тупой — просто отдаёт наружу `MailService`:

```ts
@Module({
  providers: [MailService],
  exports: [MailService],
})
export class MailModule {}
```

Импортируют его четыре модуля, которым реально надо слать письма:
`auth`, `members`, `projects`, `admin`.

## 2. Транспорт

Транспорт создаётся один раз на весь жизненный цикл сервиса — как поле
класса, а не на каждое письмо (Nodemailer сам держит пул соединений):

```ts
@Injectable()
export class MailService {
  private readonly logger = new Logger(MailService.name);

  private readonly transporter = nodemailer.createTransport(
    {
      host: process.env.SMTP_HOST,
      port: Number(process.env.SMTP_PORT),
      secure: Number(process.env.SMTP_PORT) === 465,
      auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS },
    },
    { from: process.env.SMTP_USER },   // defaults: from одинаков для всех писем
  );
```

Два момента:

- `secure` не задаётся отдельной переменной, а выводится из порта:
  465 — implicit TLS (`secure: true`), 587 — STARTTLS (`secure: false`,
  Nodemailer апгрейдит соединение сам). Одной переменной в `.env` меньше и
  нельзя выставить несогласованную пару порт/режим.
- Второй аргумент `createTransport` — это defaults для всех сообщений. `from`
  всегда равен `SMTP_USER`, потому что провайдер (Яндекс) всё равно не даст
  отправить от чужого адреса.

## 3. Переменные окружения

```
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=changeme
SMTP_PASS=changeme
APP_URL=http://localhost:5173
```

`APP_URL` — не про SMTP напрямую, но все ссылки в письмах строятся от него,
так что на каждом стенде он должен указывать на реально доступный адрес
этого окружения (на проде — `https://<домен>`), иначе письма уходят
с нерабочими ссылками.

`.env` в git не лежит, в репозитории только `.env.example` с плейсхолдерами.

## 4. Локальная разработка: Mailpit

Реально письма локально никуда не уходят. В `docker-compose.override.yml`
поднимается Mailpit, который прикидывается SMTP-сервером и складывает всё
входящее в веб-морду:

```yaml
services:
  mailpit:
    image: axllent/mailpit:latest
    ports:
      - "127.0.0.1:1025:1025"   # SMTP
      - "127.0.0.1:8025:8025"   # веб-интерфейс
```

В локальном `.env` соответственно:

```
SMTP_HOST=mailpit
SMTP_PORT=1025
```

Порт 1025 → `secure: false`, авторизация Mailpit'у безразлична. Письма
смотреть на http://127.0.0.1:8025 — там же удобно кликать ссылки
подтверждения email и сброса пароля. Реальная доставка через провайдера
проверяется только на проде.

## 5. Отправка: один приватный метод, который никогда не бросает

Все публичные методы сводятся к одному приватному `send`:

```ts
private async send(to: string, subject: string, text: string): Promise<void> {
  try {
    await this.transporter.sendMail({ to, subject, text });
  } catch (e) {
    // SMTP ещё не настроен на многих стендах разработки - не блокируем основную
    // операцию (пользователь/токен уже созданы в БД), но не молчим: логируем
    // ошибку И то, что должно было уйти письмом, чтобы разработку можно было
    // продолжать без рабочего SMTP.
    this.logger.error(`Не удалось отправить письмо на ${to}: ${(e as Error).message}`);
    this.logger.warn(`[dev] Содержимое письма "${subject}" для ${to}:\n${text}`);
  }
}
```

Смысл именно такой: падение SMTP не должно ронять регистрацию или
приглашение — пользователь и токен в базе уже созданы, письмо вторично.
Но и молчаливого проглатывания нет: в лог уходит и причина, и полный текст
письма со ссылкой, так что без рабочего SMTP можно спокойно разрабатывать —
токен верификации берётся прямо из логов backend'а.

Все письма — plain text (`text`, не `html`). HTML-шаблонов и движка шаблонов
нет вообще: тела писем собираются обычными шаблонными строками прямо в
методах.

## 6. Как это вызывают

Раз `send` не бросает, вызовы из бизнес-логики специально **не** await'ятся —
это fire-and-forget, чтобы HTTP-ответ не ждал SMTP-раунда:

```ts
// auth.service.ts - регистрация
const token = await this.actionTokens.issue(user.id, 'EMAIL_VERIFY', EMAIL_VERIFY_TTL_MS);
this.mailService.sendVerificationEmail(user.email, user.name, token);
return { id: user.id, email: user.email, name: user.name };
```

Тот же приём в `invitations.service.ts` и `members.service.ts` — там это
отмечено комментарием, чтобы никто «не починил» отсутствующий await.

Сами письма — тонкие обёртки, которые знают только про адрес ссылки и текст:

```ts
async sendVerificationEmail(email: string, name: string, token: string): Promise<void> {
  const link = `${process.env.APP_URL}/verify-email?token=${token}`;
  await this.send(
    email,
    'Подтверждение регистрации в Тезис',
    `Здравствуйте, ${name}!\n\nПодтвердите email, перейдя по ссылке (действует 24 часа):\n${link}\n\n...`,
  );
}
```

Важно: в письмо уходит **сырой** токен, а в БД (`action_token`) лежит только
его SHA-256 (`common/crypto/hash-token.util.ts`). Токен — 32 случайных байта
в hex, одноразовый (`used_at`) и с TTL: 24 часа на верификацию email,
1 час на сброс пароля.

## 7. Полный список писем

| Метод | Повод |
|---|---|
| `sendVerificationEmail` | регистрация / повторная отправка подтверждения |
| `sendPasswordResetEmail` | «Забыли пароль?» |
| `sendEmailChangeVerification` | подтверждение нового адреса при смене email |
| `sendEmailChangeNotice` | уведомление на **старый** адрес о запросе смены |
| `sendInvitationEmail` | приглашение в проект (роль редактора/читателя) |
| `sendRoleChangedEmail` | роль в проекте изменена |
| `sendAccessRevokedEmail` | доступ к проекту отозван |
| `sendOwnershipTransferredEmail` | вы стали владельцем проекта |
| `sendOwnershipTransferredNotice` | вы передали владение (или это сделал админ) |
| `sendAccountBlockedEmail` | учётная запись заблокирована, с причиной |
| `sendProjectForceDeletedEmail` | проект удалён администратором, с причиной |

## 8. Грабли, на которые уже наступили

- **Порт 25 закрыт у хостеров** — только внешний SMTP по 465/587.
- **Исходящий SMTP заблокирован по умолчанию.** На свежем VPS провайдер
  режет исходящий SMTP даже на 465/587. Снимается тикетом в поддержку —
  это не ошибка конфигурации, и по логам выглядит как таймаут на ровном месте.
- **Яндекс.Почта отвечает `535 no access rights`**, если в настройках ящика
  не включён доступ по IMAP/POP3. Это общий переключатель для любого
  внешнего SMTP-клиента, не только для нашего.
- **Тихий dev-фолбэк — плохая идея.** Раньше ошибка отправки просто
  проглатывалась, и диагностика «почему не приходит письмо» стоила времени.
  Отсюда в `send` два лога: `error` с причиной и `warn` с телом письма.
