
# Order Processing System for a Multi-Vendor E-Commerce Platform

## Overview
This project is a serverless, event-driven order processing system for a multi-vendor e-commerce platform, built on AWS Lambda, API Gateway, EventBridge, and DynamoDB. It supports:
- Order placement and management
- Vendor inventory updates
- Payment processing
- Notifications
- Centralized logging, error handling, and idempotency
- DLQ and replay for failed events
- Role-based and username-password authentication via a custom Lambda Authorizer


## Architecture
- **API Gateway**: Exposes REST endpoints for orders, inventory, and payments.
- **Lambda Functions**: Modular handlers for each business domain (order, inventory, payment, notification).
- **EventBridge**: Publishes and routes business events (e.g., OrderPlaced).
- **DynamoDB**: Stores orders, inventory, payments, and idempotency keys.
- **DLQ**: Handles failed events for replay.
- **AWS Secrets Manager**: Securely stores user credentials and roles for Lambda authorizer.

---

## System Diagrams

### 1. High-Level Architecture Diagram

```mermaid
flowchart LR
    APIGW[API Gateway]
    ORDER_LAMBDA[Order Lambda Producer]
    EVENTBRIDGE[EventBridge]
    DDB[DynamoDB]
    AUTH[Lambda Authorizer]
    SECRETS[AWS Secrets Manager]
    CW[CloudWatch]
    INV_CONSUMER[Inventory Consumer]
    PAY_CONSUMER[Payment Consumer]
    NOTIF_CONSUMER[Notification Consumer]
    DLQ_INV[DLQ: Inventory]
    DLQ_PAY[DLQ: Payment]
    DLQ_NOTIF[DLQ: Notification]

    APIGW -->|REST Calls| ORDER_LAMBDA
    ORDER_LAMBDA -->|Events| EVENTBRIDGE
    ORDER_LAMBDA -->|DynamoDB Ops| DDB
    ORDER_LAMBDA -->|Auth| AUTH
    AUTH -->|User Secrets| SECRETS
    ORDER_LAMBDA -->|Logs| CW
    EVENTBRIDGE -->|OrderPlaced| INV_CONSUMER
    EVENTBRIDGE -->|OrderPlaced| PAY_CONSUMER
    EVENTBRIDGE -->|OrderPlaced| NOTIF_CONSUMER
    INV_CONSUMER -->|Update| DDB
    PAY_CONSUMER -->|Record| DDB
    NOTIF_CONSUMER -->|Send| CW
    INV_CONSUMER -->|DLQ| DLQ_INV
    PAY_CONSUMER -->|DLQ| DLQ_PAY
    NOTIF_CONSUMER -->|DLQ| DLQ_NOTIF
```

*Note: Text-based AWS resource names are used for maximum compatibility. For official AWS icons, see https://aws.amazon.com/architecture/icons/*

### 1a. Low Level Architectural Diagram

```mermaid
flowchart TD
    subgraph API Layer
        APIGW[API Gateway]
    end
    subgraph Auth
        AUTH[Lambda Authorizer]
    end
    subgraph Lambda Handlers
        ORD_H[Order Handler]
        INV_H[Inventory Handler]
        PAY_H[Payment Handler]
    end
    subgraph Services
        ORD_S[Order Service]
        INV_S[Inventory Service]
        PAY_S[Payment Service]
    end
    subgraph DAO
        ORD_DAO[Order DAO]
        INV_DAO[Inventory DAO]
        PAY_DAO[Payment DAO]
    end
    subgraph Shared_Common
        LOG[Logger]
        EXC[Exceptions]
        IDMP[Idempotency]
        VAL[Validation]
        DLQ[DLQ Replay]
    end
    APIGW -->|auth| AUTH
    APIGW --> ORD_H
    APIGW --> INV_H
    APIGW --> PAY_H
    AUTH --> ORD_H
    AUTH --> INV_H
    AUTH --> PAY_H
    ORD_H --> ORD_S
    INV_H --> INV_S
    PAY_H --> PAY_S
    ORD_S --> ORD_DAO
    INV_S --> INV_DAO
    PAY_S --> PAY_DAO
    ORD_H --> LOG
    INV_H --> LOG
    PAY_H --> LOG
    ORD_H --> EXC
    INV_H --> EXC
    PAY_H --> EXC
    ORD_H --> IDMP
    INV_H --> IDMP
    PAY_H --> IDMP
    ORD_H --> VAL
    INV_H --> VAL
    PAY_H --> VAL
    ORD_H --> DLQ
    INV_H --> DLQ
    PAY_H --> DLQ
```

*This diagram shows the flow from API Gateway through Lambda handlers, services, DAOs, and shared/common utilities, emphasizing modularity and separation of concerns.*

### 2. Functional Block Diagram

```mermaid
flowchart TD
    subgraph API Layer
        APIGW[API Gateway]
    end
    subgraph Auth
        AUTH[Lambda Authorizer]
    end
    subgraph Business Logic
        ORD[Order Handler]
        INV[Inventory Handler]
        PAY[Payment Handler]
    end
    subgraph Eventing
        EVB[EventBridge]
        DLQ[DLQ]
    end
    subgraph Data
        DDB[DynamoDB]
    end
    APIGW -->|auth| AUTH
    APIGW --> ORD
    APIGW --> INV
    APIGW --> PAY
    ORD --> EVB
    INV --> EVB
    PAY --> EVB
    EVB --> DLQ
    ORD --> DDB
    INV --> DDB
    PAY --> DDB
```

### 3. Sequence Diagram: Order Placement

```mermaid
sequenceDiagram
    participant U as User
    participant API as API Gateway
    participant AUTH as Lambda Authorizer
    participant ORD as Order Lambda
    participant DDB as DynamoDB
    participant EVB as EventBridge
    participant INV as Inventory Consumer
    participant PAY as Payment Consumer
    U->>API: POST /orders
    API->>AUTH: Authorize
    AUTH-->>API: Policy
    API->>ORD: Invoke Lambda
    ORD->>DDB: Create Order (Transact)
    ORD->>EVB: Publish OrderPlaced Event
    EVB->>INV: Trigger Inventory Consumer
    EVB->>PAY: Trigger Payment Consumer
    INV->>DDB: Update Inventory
    PAY->>DDB: Record Payment
```

---

## Setup & Deployment
1. **Clone the repository**
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set environment variables** for each Lambda:
   - `ORDERS_TABLE`, `INVENTORY_TABLE`, `PAYMENTS_TABLE`, `IDEMPOTENCY_TABLE`
   - `EVENT_BUS_NAME`
   - `AUTH_TOKEN` (for demo Bearer token)
   - `AWS_REGION` (for Secrets Manager region)
   - User credentials and roles are now securely managed in AWS Secrets Manager (see below).
4. **Deploy Lambdas and API Gateway**
   - Use AWS Console, SAM, or Serverless Framework
   - Attach the custom authorizer to protected endpoints
5. **Configure EventBridge rules** to route `OrderPlaced` events to consumers
6. **Set up DLQs** for all consumers and wire replay handlers

## API Endpoints & Sample Requests

### Order Placement
- **POST** `/orders`
- **Authorization**: `Basic` (admin:password)
- **Request**
  ```json
  {
    "customerId": "cust123",
    "items": [
      {"vendorId": "v1", "productId": "p1", "quantity": 2}
    ]
  }
  ```
- **Response**
  ```json
  {"success": true, "orderId": "..."}
  ```

### Inventory Update
- **POST** `/inventory`
- **Authorization**: `Bearer demo-token`
- **Request**
  ```json
  {"vendorId": "v1", "productId": "p1", "quantity": 10}
  ```
- **Response**
  ```json
  {"success": true, "vendorId": "v1", "productId": "p1"}
  ```

### Payment Processing
- **POST** `/payments`
- **Authorization**: `Bearer demo-token`
- **Request**
  ```json
  {"orderId": "order123", "amount": 100, "paymentMethod": "credit_card"}
  ```
- **Response**
  ```json
  {"success": true, "orderId": "order123"}
  ```

## Error Response Format
```json
{
  "errorCode": "BAD_REQUEST",
  "errorMessage": "Bad request",
  "timestamp": "...",
  "recommendedData": {"details": "..."}
}
```

## Swagger/OpenAPI
- [Swagger Editor](https://editor.swagger.io/)
- Example OpenAPI snippet:
```yaml
openapi: 3.0.1
info:
  title: Order Processing API
  version: 1.0.0
paths:
  /orders:
    post:
      summary: Place an order
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/OrderRequest'
      responses:
        '201':
          description: Order placed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrderResponse'
      security:
        - basicAuth: []
components:
  schemas:
    OrderRequest:
      type: object
      properties:
        customerId:
          type: string
        items:
          type: array
          items:
            type: object
            properties:
              vendorId:
                type: string
              productId:
                type: string
              quantity:
                type: integer
    OrderResponse:
      type: object
      properties:
        success:
          type: boolean
        orderId:
          type: string
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic
```

## Recommendations
- Use AWS SAM or Serverless Framework for repeatable deployments.
- Set up CloudWatch Alarms for error monitoring.
- Use AWS X-Ray for distributed tracing.
- Regularly test DLQ and replay logic.
- Add event versioning for future-proofing.
- Store user credentials and roles in AWS Secrets Manager as JSON objects (e.g., `{ "password_hash": "...", "role": "admin" }`).
- Never store or compare plain-text passwords; always use salted hashes.

---
For more details, see the code and comments in each module. Contributions and improvements are welcome!




