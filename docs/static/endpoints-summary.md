# API Endpoints Summary

| Method | Endpoint | Summary | Tags |
|--------|----------|---------|------|
| GET | `/webhook` | Verify WhatsApp Webhook | WhatsApp Webhooks |
| POST | `/webhook` | Handle WhatsApp Messages | WhatsApp Webhooks |
| GET | `/health` | System Health Check | WhatsApp Webhooks |
| GET | `/stats` | System Statistics | WhatsApp Webhooks |
| POST | `/force-process-batch/{user_id}` | Force Process Message Batch | WhatsApp Webhooks |
| GET | `/whatsapp/webhook` | Whatsapp Webhook Verify | WhatsApp |
| POST | `/whatsapp/webhook` | Whatsapp Webhook Handler | WhatsApp |
| GET | `/whatsapp/health` | Whatsapp Health | WhatsApp |
| POST | `/whatsapp/test-template/{phone_number}` | Test Template Message | WhatsApp |
| GET | `/` | API Information |  |
| GET | `/test` | Test Whatsapp Api |  |

## Tags Description

- **WhatsApp Webhooks**: Core webhook endpoints for WhatsApp message processing
- **Assessment Report Management**: Administrative endpoints for report status management
- **Health & Monitoring**: System health and performance monitoring endpoints
