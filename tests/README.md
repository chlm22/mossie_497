# Mossie Login Interface Tests

This directory contains test cases for the Mossie login interface project with PostgreSQL backend authentication.

## Test Cases Overview

The test suite includes 10 comprehensive test cases:

1. **User Registration Test**: Verifies successful user registration
2. **Duplicate Username Test**: Tests handling of duplicate username registration attempts
3. **Successful Login Test**: Verifies correct authentication behavior
4. **Failed Login Test**: Tests rejection of invalid credentials
5. **Last Login Timestamp Test**: Verifies timestamps are updated on login
6. **Password Reset Request Test**: Tests token generation functionality
7. **Password Reset with Valid Token**: Verifies password reset with valid token
8. **Password Reset with Expired Token**: Tests rejection of expired tokens
9. **Session Protection Test**: Verifies protected routes require authentication
10. **SQL Injection Protection Test**: Tests resistance to SQL injection attempts

## Test Setup

### Prerequisites

- Python 3.6+
- PostgreSQL database
- A test database named `mossie_test` (create it first)

### Installation

1. Install test dependencies:
   ```
   pip install -r tests/requirements_test.txt
   ```

2. Create a test database:
   ```
   createdb mossie_test
   ```

## Running Tests

Run all tests:
```
pytest -v
```

Run specific test class:
```
pytest -v tests/test_auth.py::TestLogin
```

Run specific test:
```
pytest -v tests/test_auth.py::TestLogin::test_successful_login
```

## Test Database

The tests will:
- Automatically create necessary tables in the test database
- Clean up after tests complete
- Use unique usernames to avoid conflicts between test runs

## Notes

- The tests use a separate database (`mossie_test`) from your development or production database.
- Make sure PostgreSQL is running when executing tests.
- Each test operates in isolation - database state is reset between tests.
