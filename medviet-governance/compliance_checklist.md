# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [x] Backup cũng phải ở trong lãnh thổ VN
- [x] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training
- [x] Có mechanism để user rút consent (Right to Erasure)
- [x] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [x] Có incident response plan
- [x] Alert tự động khi phát hiện breach
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
- [x] DPO có thể liên hệ tại: dpo@medviet.vn

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | AES-256-GCM envelope encryption (SimpleVault) | ✅ Done | Infra Team |
| Audit logging | FastAPI middleware ghi log mọi request kèm user/role/timestamp | ✅ Done | Platform Team |
| Breach detection | Prometheus alert rule khi detection rate giảm hoặc có truy cập bất thường | ✅ Done | Security Team |

## F. Technical Solutions cho các mục đã hoàn thành

### Audit Logging
Implement FastAPI middleware ghi structured log (JSON) cho mỗi request:
- Thông tin: `timestamp`, `user`, `role`, `method`, `path`, `status_code`, `ip`
- Lưu vào file `logs/api_access.log` với rotation theo ngày
- Forward sang ELK Stack hoặc Grafana Loki để query và alert

```python
# Ví dụ middleware
@app.middleware("http")
async def audit_log(request: Request, call_next):
    response = await call_next(request)
    log.info({
        "timestamp": datetime.utcnow().isoformat(),
        "user": request.headers.get("Authorization", "anonymous"),
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "ip": request.client.host,
    })
    return response
```

### Breach Detection
Dùng Prometheus + Grafana (đã có trong `docker-compose.yml`):
- Alert khi: số request 403 tăng đột biến (> 50/phút) → có thể là brute-force
- Alert khi: PII detection rate giảm xuống dưới 90% → pipeline bị lỗi
- Alert khi: có truy cập vào `/api/patients/raw` ngoài giờ hành chính
- Runbook 72h: on-call engineer nhận alert → đánh giá → báo cáo Bộ TT&TT nếu cần
