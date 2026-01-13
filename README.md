
# API Naturalize - Backend & Dashboard Integration

This API handles authentication and dashboard management for the Naturalize platform. It supports role-based access control, specifically distinguishing between regular users and administrative accounts.

## 🛠 Setup & Configuration

To run this project, you need to configure your environment variables. You can customize the database settings and security keys as per your requirements.

### 1. Environment Variables
Create a `.env` file in the root directory and update it with your own values:

```env
# Database Configuration
MONGODB_URL=your_mongodb_connection_string
DATABASE_NAME=your_preferred_db_name

# Security
SECRET_KEY=your_custom_secret_key
ALGORITHM=HS256

```

---

## 🔐 User Registration & Admin Access

The system automatically assigns roles based on the endpoint used during registration.

### 1. How to Create a Regular User

Standard users (Default Users) can sign up through the main auth endpoint.

* **Endpoint:** `POST /auth/`
* **Payload:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "user@example.com",
  "phone_number": "123456789",
  "password": "securepassword"
}

```


* **Note:** This user will automatically be assigned the `default` role.

### 2. How to Create an Admin User (Connect with DashAdmin)

To access the **DashAdmin** dashboard, a user must be created as an administrator.

* **Endpoint:** `POST /auth/signup/admin`
* **Payload:** Same as above.
* **Effect:** This endpoint automatically assigns the `ADMIN` role, allowing the user to log in and manage the dashboard.

---

## Deployment Steps

### 1. Database & UI Setup

You can deploy your MongoDB instance and use **Mongo Express** to visualize the data.

1. Deploy **MongoDB** (ensure the URL matches your `.env` file).
2. Deploy **Mongo Express** and connect it to the same MongoDB instance.
3. Once the API is running, use the **Admin Signup** endpoint to create your first dashboard administrator.

### 2. OTP Verification

After any user (Regular or Admin) signs up, they must verify their account using the OTP sent to their email.

* **Endpoint:** `POST /auth/otp_verify`
* **Required Data:** `email` and `otp`.

---

## 📁 Key API Endpoints

| Feature | Method | Endpoint |
| --- | --- | --- |
| **Default Signup** | `POST` | `/auth/` |
| **Admin Signup** | `POST` | `/auth/signup/admin` |
| **Login** | `POST` | `/auth/login` |
| **Verify OTP** | `POST` | `/auth/otp_verify` |


