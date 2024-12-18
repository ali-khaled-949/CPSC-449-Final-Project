# Cloud Service Access Management System

## Project Description
This project implements a **Cloud Service Access Management System** using **FastAPI**. The system dynamically manages access to various cloud services based on user subscriptions. Admins can create and manage subscription plans, set permissions, and enforce usage limits, while customers can subscribe to plans, track their usage, and access cloud services within their allocated limits.

---

## Key Features
### 1. Subscription Plan Management
- **Admin Functions**:
  - Create, modify, and delete subscription plans.
  - Define permissions (API endpoints) and usage limits per plan.
- **Endpoints**:
  - `POST /plans` - Create a new plan.
  - `PUT /plans/{plan_id}` - Modify an existing plan.
  - `DELETE /plans/{plan_id}` - Delete a plan.

### 2. Permission Management
- **Admin Functions**:
  - Add, modify, and delete permissions.
  - Define API endpoints and descriptions for permissions.
- **Endpoints**:
  - `POST /permissions` - Add a new permission.
  - `PUT /permissions/{permissionId}` - Modify an existing permission.
  - `DELETE /permissions/{permissionId}` - Delete a permission.

### 3. User Subscription Handling
- **Customer Functions**:
  - Subscribe to a plan.
  - View subscription details and usage statistics.
- **Admin Functions**:
  - Assign or update user subscription plans.
- **Endpoints**:
  - `POST /subscriptions` - Subscribe a user to a plan.
  - `PUT /subscriptions/{user_id}` - Modify a user's subscription plan.
  - `GET /subscriptions/{user_id}` - View subscription details.
  - `GET /subscriptions/{user_id}/usage` - View usage statistics.

### 4. Access Control
- **Functionality**:
  - Check if an API request is within the user's subscription permissions and usage limits.
  - Deny access if limits are exceeded or the API is not allowed in the plan.
- **Endpoints**:
  - `GET /access/{user_id}/{api_request}` - Check access permissions.

### 5. Usage Tracking and Limit Enforcement
- **Functionality**:
  - Track the number of API requests made by users.
  - Temporarily restrict access to APIs once usage limits are reached.
- **Endpoints**:
  - `POST /usage/{userId}` - Track API usage.
  - `GET /usage/{userId}/limit` - Check usage limits and status.

### 6. Simulated Cloud Services
- **Dummy Services**: Six cloud service APIs are provided for demonstration purposes:
  - `GET /api/service1`
  - `GET /api/service2`
  - `GET /api/service3`
  - `GET /api/service4`
  - `GET /api/service5`
  - `GET /api/service6`

---

## Technologies Used
- **Python** with **FastAPI** for backend development
- **SQLAlchemy** for ORM and database management
- **MySQL** for the database (configurable via environment variables)
- **Pydantic** for data validation
- **Uvicorn** for server deployment

---

## Installation Instructions
Follow these steps to set up and run the project:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/cloud-service-access-management.git
   cd cloud-service-access-management
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Mac/Linux
   venv\Scripts\activate    # On Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   - Create a `.env` file in the root directory and add the following:
     ```
     DATABASE_URL=mysql+pymysql://username:password@host:port/dbname
     ```
     Replace `username`, `password`, `host`, `port`, and `dbname` with your MySQL database credentials.

5. **Run the Application**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   The application will be available at `http://localhost:8000`.

6. **Access API Documentation**:
   - FastAPI provides interactive API docs:
     - Swagger UI: `http://localhost:8000/docs`
     - Redoc: `http://localhost:8000/redoc`

---

## Testing the API
You can test the endpoints using **Postman** or any REST client:

### Example Requests:
- **Create a Plan**:
  - Endpoint: `POST /plans`
  - Body:
    ```json
    {
      "name": "Basic Plan",
      "description": "Access to basic services",
      "api_permissions": ["service1", "service2"],
      "usage_limit": 100
    }
    ```

- **Subscribe a User**:
  - Endpoint: `POST /subscriptions`
  - Body:
    ```json
    {
      "user_id": "user123",
      "plan_id": 1
    }
    ```

- **Check Access**:
  - Endpoint: `GET /access/{user_id}/{api_request}`
  - Example: `GET /access/user123/service1`

---

## Project Structure
```
.
├── main.py                # Application entry point
├── models.py              # Database models (optional separation)
├── requirements.txt       # Project dependencies
├── .env                   # Environment variables
└── README.md              # Documentation
```

---

## Author
- **Name**: Ali Khaled
- **Email**: [alikhaled@csu.fullerton.edu](mailto:alikhaled@csu.fullerton.edu)

---

## Future Improvements
- Add authentication using OAuth2.
- Implement rate-limiting for API requests.
- Provide detailed analytics for usage tracking.

---

## License
This project is licensed under the MIT License.
