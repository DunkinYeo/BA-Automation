# BioArmour 자동화 이슈 목록

> 작성일: 2026-05-14  
> 테스트 환경: Pixel 7 (55ETQWBXYE1RA1) / BioArmour 웨어러블 S/N: 260508

---

## 이슈 구분 기준
- ✅ **해결됨** — 코드 수정 완료
- 🔍 **확인 중** — 재테스트 또는 실제 팝업 텍스트 확인 필요
- ❌ **미해결** — 원인 파악 중

---

## 자동화 코드 이슈

| 이슈 ID | 상태 | 관련 TC | 증상 | 원인 | 조치 |
|---------|------|---------|------|------|------|
| CODE-01 | ✅ | LOGIN-004, ERR-10/11/01 | 시리얼 입력 후 "연결하기" 버튼 tap 실패 | `enter_serial` 실행 후 키보드가 내려가지 않아 버튼이 가려짐 | `enter_serial` 끝에 `hide_keyboard()` 추가 |
| CODE-02 | ✅ | LOGIN-004, ERR-10/11/01 | `_clear_serial`이 입력값을 못 지움 | 포커스 없이 DEL 키만 전송 | 입력 영역 탭 → DEL 6회 → `hide_keyboard()` 순서로 수정 |
| CODE-03 | ✅ | LOGIN-006 | 잘못된 시리얼 에러 팝업 감지 실패 | 앱 팝업 실제 텍스트가 "알 수 없는 오류 (902)"로, 기댓값 목록에 미포함 | 실제 텍스트("알 수 없는 오류", "902") login.py 기댓값에 추가 완료 |
| CODE-04 | ✅ | SET-001~007 | 설정 서브화면에서 설정 메인으로 오인 | `_on_setting`이 "버전 정보" 타이틀 하나만 감지해 서브화면을 메인으로 판정 | 3개 항목 동시 존재 여부로 판정하도록 수정, `_ensure_setting` 함수 추가 |
| CODE-05 | ✅ | EXAM-006 | 검사 종료 팝업 체크박스 클릭 실패 | `android.widget.CheckBox` 클래스로 조회했으나 React Native 커스텀 컴포넌트 | content-desc="검사를 종료하겠습니다." XPath로 교체 |
| CODE-06 | ✅ | EXAM-SET-001 | 검사 화면 설정 아이콘 tap 실패 | `tap_text("설정")`으로 시도했으나 아이콘에 텍스트 라벨 없음 | 로그인 화면과 동일한 좌표(977, 238) 탭으로 교체 |
| CODE-07 | ✅ | LOGIN-ERR-10/11/01 + 이후 전체 | GPS/BT/WiFi OFF 테스트 후 BLE 연결 성공 시 앱이 "검사 정보 확인"에 남아 이후 TC 전체 도미노 실패 | 에러 TC finally 블록에 로그인 복귀 로직 없음 + `_force_end_exam_to_login`이 해당 화면 미처리 | 에러 TC 3개 finally에 `_back_to_login()` 추가 + `_force_end_exam_to_login` 최상단에 "검사 정보 확인" 처리 추가 |
| CODE-08 | ✅ | LOGIN-ERR-11 | OS 위치 권한 팝업("허용"/"앱 사용 중에만 허용")이 테스트 흐름을 간헐적으로 차단 | `no_reset:true` 환경에서 앱 위치 권한이 미부여 상태로 남을 수 있음 | `reset_to_login` 시 `pm grant`로 사전 부여 + `_dismiss_os_permission_dialog` 추가 |
| CODE-10 | ✅ | 전체 | 앱 백그라운드 상태에서 Appium 세션 시작 시 다른 앱을 제어 — BioArmour 대신 포그라운드 앱에 붙음 | `no_reset:true`일 때 Appium이 앱 포그라운드 전환을 보장하지 않음 | `AndroidDriver.__init__`에 `_ensure_app_foreground()` 추가 — 세션 연결 직후 `current_package` 확인 후 불일치 시 `bring_to_foreground()` 호출 |
| CODE-09 | ✅ | EXAM-003 | '검사 시작' 클릭 후 '검사 종료' 버튼 감지 타임아웃 (11.9s) — 버튼은 실제로 표시됨 | 검사 시작 후 로딩 오버레이가 10s 이상 유지돼 `is_visible_text` timeout=10 초과 | `test_exam_003_start_exam`에 `_wait_loading_clear(30s)` 추가 + timeout 10s → 20s 증가 |

---

## 앱 동작 확인 필요 사항 (→ APP_ISSUES.md 참조)

| 이슈 ID | 상태 | 관련 TC | 내용 |
|---------|------|---------|------|
| APP-01 | ⚠️ | LOGIN-006, ERR-03 | 잘못된 시리얼 → "알 수 없는 오류 (902)" 팝업 표시 (사용자 친화적 메시지 아님) |
| APP-02 | 🔍 | ERR-11 | GPS OFF 에러 팝업 정확한 텍스트 미확인 |
| APP-03 | 🔍 | ERR-10 | 블루투스 OFF 에러 팝업 정확한 텍스트 미확인 |
| APP-04 | 🔍 | ERR-01 | WiFi OFF 에러 팝업 정확한 텍스트 미확인 |
| APP-05 | ⚠️ | LOGIN-002 | 시리얼 미입력 시 "연결하기" 버튼 `enabled`/`clickable` 모두 true 반환 — 비활성화 상태 접근성 속성 미반영 |
| APP-07 | ⚠️ | LOGIN-ERR-10/11/01 이후 연속 테스트 | BLE 세션 남은 상태에서 재연결 시 "알 수 없는 오류 (302)" 팝업 — 팝업 닫으면 정상 진행 가능 |
| APP-06 | ⚠️ | LOGIN-ERR-11, EXAM-ERR-02 | GPS OFF 상태에서도 BLE 연결 성공 후 앱 진행 가능 — 로그인/검사 단계 모두에서 GPS 에러 팝업 미표시 |

---

## 업데이트 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-14 | CODE-01, CODE-02 해결 (`enter_serial`, `_clear_serial` 수정) |
| 2026-05-14 | CODE-03 해결 — 실제 팝업 텍스트 "알 수 없는 오류 (902)" 스크린샷으로 확인, login.py 기댓값 업데이트 |
| 2026-05-14 | CODE-04 해결 — 설정 화면 `_on_setting` 판정 로직 수정, `_ensure_setting` 추가 |
| 2026-05-14 | CODE-05 해결 — 검사 종료 팝업 체크박스 content-desc 기반으로 교체 |
| 2026-05-14 | CODE-06 해결 — 검사 화면 설정 아이콘 좌표 탭으로 교체 |
| 2026-05-14 | APP-01~05 확인 및 APP_ISSUES.md 개발팀 전달용으로 정리 |
| 2026-05-14 | CODE-07 해결 — `_force_end_exam_to_login`에 "검사 정보 확인" 화면 복귀 로직 추가 |
| 2026-05-14 | CODE-08 추가 — OS 위치 권한 팝업 처리: `pm grant` 사전 부여 + `_dismiss_os_permission_dialog` |
| 2026-05-14 | APP-06 발견 — GPS OFF 상태에서도 BLE 연결/검사 진행 가능, 로그인+검사 단계 모두 GPS 에러 팝업 미표시 |
| 2026-05-14 | CODE-09 해결 — EXAM-003 검사 시작 후 `_wait_loading_clear` + timeout 20s |
| 2026-05-14 | CODE-10 해결 — 앱 백그라운드 시 다른 앱 제어 문제, `_ensure_app_foreground()` 추가 |
