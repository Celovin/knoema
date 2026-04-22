# Toss Payments 가맹점 온보딩 체크리스트

이 문서는 Celovin 개인사업자 기준의 Toss Payments 국내 결제 온보딩 참고자료다. 실제 가입, 심사, 계약, 실결제 키 발급은 사용자가 직접 진행해야 한다.

## 1. 공식 근거

- Toss Payments PG 서비스: https://www.tosspayments.com/services
- Toss Payments API 키 문서: https://docs.tosspayments.com/reference/using-api/api-keys
- Toss Pay 오프라인 청약 가이드의 개인사업자 서류 예시: https://docs-pay.toss.im/offline/prepare/subscription/agency

온라인 PG 신청의 최종 요구사항은 Toss Payments 상점관리자와 계약 담당자의 안내가 우선한다.

## 2. 가입 전 준비

| 항목 | 준비 상태 |
| --- | --- |
| 사업자등록증 | 개인사업자 등록번호, 상호, 대표자명, 사업장 주소가 최신인지 확인 |
| 대표자 신분증 | 주민등록번호 뒷자리 등 불필요 정보 마스킹 가능 여부를 계약 담당자에게 확인 |
| 정산 계좌 사본 | 사업자명 또는 대표자명과 계좌 예금주 일치 여부 확인 |
| 웹사이트 URL | 서비스 설명, 가격, 환불 정책, 개인정보처리방침, 고객 문의 채널이 접근 가능해야 함 |
| 상업 문서 | `docs/legal.md`, `legal/commercial_terms_v1_ko.md`, `legal/privacy_policy_v1_ko.md`, `legal/refund_cancellation_policy_v1_ko.md` 초안을 법률 검토 후 게시 |

## 3. 신청 흐름

1. Toss Payments 사이트에서 온라인 결제 또는 PG 서비스 이용 신청을 시작한다.
2. Celovin 개인사업자 정보를 입력한다.
3. 웹사이트 URL, 판매 상품 설명, 가격, 환불 기준, 고객지원 이메일을 제출한다.
4. 요청받은 사업자등록증, 대표자 신분증, 정산 계좌 자료를 업로드한다.
5. 심사 중 반려 사유가 오면 아래 체크리스트를 기준으로 보완한다.
6. 계약이 완료되면 상점관리자와 개발자센터에서 테스트 키와 운영 키를 확인한다.
7. 운영 키는 `.env.local` 또는 배포 환경의 secret store에만 저장한다.

## 4. API 키 구조와 환경 변수

Toss Payments API 키 문서는 클라이언트 키와 시크릿 키가 세트로 발급된다고 설명한다. 시크릿 키는 외부에 노출되면 안 되며 GitHub, 클라이언트 코드, 문서에 넣지 않는다.

Knoema 환경 변수 명명:

```text
TOSS_CLIENT_KEY=
TOSS_SECRET_KEY=
```

운영 원칙:

- `TOSS_CLIENT_KEY`는 결제 위젯 또는 프런트엔드 초기화에 필요한 공개 가능 키인지 계약 상품별로 확인한다.
- `TOSS_SECRET_KEY`는 서버 전용이다.
- 테스트 키와 운영 키는 같은 변수명에 환경별 secret store로 분리한다.
- 키가 외부에 노출되면 즉시 Toss Payments 상점관리자에서 교체하고 배포 secret을 갱신한다.

## 5. 흔한 반려 사유 체크리스트

- 웹사이트가 비공개이거나 결제 상품 설명이 모호함.
- 가격, 환불 기준, 고객지원 채널이 보이지 않음.
- 개인정보처리방침 대신 부정확한 명칭이나 미완성 문서가 게시됨.
- 사업자등록증의 상호와 사이트 운영 주체가 일치하지 않음.
- 정산 계좌 예금주가 사업자 또는 대표자 정보와 맞지 않음.
- AI, 시뮬레이션, 연구 도구의 사용 제한과 금지 사용처가 충분히 설명되지 않음.
- 실서비스 URL이 임시 페이지, 비밀번호 페이지, 또는 개발 서버 주소임.

## 6. 제출 전 자체 점검

```powershell
.venv\Scripts\python.exe scripts\check_payment_env.py
```

이 스크립트는 키 값이 아니라 설정 여부만 출력한다. 실키를 생성하기 전에는 unset 상태가 정상이다.
