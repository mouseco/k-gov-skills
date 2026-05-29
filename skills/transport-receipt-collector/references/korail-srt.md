# Korail/SRT Receipt Provider Notes

This public note intentionally avoids listing internal Korail mobile URLs, endpoint names, request fields, or captured parameters.

## Scope

- SRT: automate the public purchase-history/receipt page where account login and additional verification are permitted by the user.
- KTX/Korail: install the `ktx-booking` skill first, point `KGOV_KORAIL_CONNECTOR` to a local receipt connector that uses that skill's helper, then save a KorailTalk-style receipt PNG and redacted JSON.

## Public boundary

Do not publish:

- Internal mobile endpoint URLs
- Endpoint class names
- Request parameter names
- Captured request/response payloads
- Ticket tokens, card numbers, approval numbers, account identifiers, or authentication material

The public repository may document the workflow shape and connector contract, but not Korail internal endpoint/request details. The expected private connector should reuse the helper shipped with the `ktx-booking` skill.

## Connector contract

A Korail local connector should normally import or otherwise reuse the `ktx-booking` skill helper. It should:

1. Authenticate using local account configuration.
2. Query the requested date range.
3. Select the requested row index.
4. Save a redacted JSON file and a KorailTalk-style PNG file.
5. Print a JSON summary to stdout.

Expected stdout shape:

```json
{
  "provider": "korail-app-api",
  "range": { "startDate": "YYYY-MM-DD", "endDate": "YYYY-MM-DD" },
  "rowIndex": 1,
  "output": {
    "jsonPath": "outputs/receipts/YYYY-MM/example.json",
    "pngPath": "outputs/receipts/YYYY-MM/example.png",
    "imageSource": "local-connector"
  },
  "status": "receipt_saved"
}
```

Use `KGOV_KORAIL_CONNECTOR` to point the public wrapper to the local receipt connector script, for example:

```powershell
$env:KGOV_KORAIL_CONNECTOR="$HOME\.openclaw\private-connectors\korail_receipt_connector.py"
```

## Safety rules

- Stop on CAPTCHA, OTP, extra mobile verification, certificate prompts, payment, cancellation, refund, or account-change flows.
- Keep raw connector responses out of public logs.
- Store only redacted JSON.
- Prefer the official app/site saved image when a filing authority requires exact first-party output.

## SRT notes

SRT support uses the public purchase-history and receipt page flow. If login or verification changes, stop and ask the user to complete the required step manually.
