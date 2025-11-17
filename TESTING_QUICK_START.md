# Testing Quick Start Guide

Quick reference for running tests in the Budget Pulse application.

## Prerequisites

Make sure you're in the project root and have the virtual environment activated:

```powershell
# Navigate to project root
cd C:\Users\mhmts\PycharmProjects\expense-manager-web-app

# Activate virtual environment (if not already active)
.\.venv\Scripts\Activate.ps1
```

---

## Running Tests

### Option 1: Simple Command (Recommended)

From the project root, just run:

```powershell
pytest tests/unit/ -v
```

This works because we've configured `pythonpath = .` in `pytest.ini`.

### Option 2: Using Python Module

```powershell
python -m pytest tests/unit/ -v
```

This automatically adds the current directory to Python path.

### Option 3: Run All Tests

```powershell
pytest tests/ -v
```

---

## Common Test Commands

### Run Specific Test File

```powershell
pytest tests/unit/test_auth_service.py -v
```

### Run Specific Test Class

```powershell
pytest tests/unit/test_auth_service.py::TestCreateUser -v
```

### Run Specific Test Function

```powershell
pytest tests/unit/test_auth_service.py::TestCreateUser::test_create_user_success -v
```

### Run Tests with Coverage

```powershell
pytest tests/unit/ --cov=app/services --cov-report=term-missing
```

### Run Tests with Coverage (HTML Report)

```powershell
pytest tests/unit/ --cov=app/services --cov-report=html
```

Then open `htmlcov/index.html` in your browser.

### Run Tests Quietly (Less Verbose)

```powershell
pytest tests/unit/ -q
```

### Run Tests with Detailed Output

```powershell
pytest tests/unit/ -vv
```

### Run Tests and Stop on First Failure

```powershell
pytest tests/unit/ -x
```

### Run Only Failed Tests from Last Run

```powershell
pytest tests/unit/ --lf
```

### Run Tests in Parallel (Faster)

```powershell
# Install pytest-xdist first: pip install pytest-xdist
pytest tests/unit/ -n auto
```

---

## Test Categories

### Run Only Unit Tests

```powershell
pytest tests/unit/ -v
```

### Run Only Integration Tests

```powershell
pytest tests/integration/ -v
```

### Run Tests by Marker

```powershell
# Run only tests marked with @pytest.mark.unit
pytest -m unit -v

# Run only tests marked with @pytest.mark.integration
pytest -m integration -v
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'app'"

**Solution 1:** Make sure you're running from the project root:
```powershell
cd C:\Users\mhmts\PycharmProjects\expense-manager-web-app
pytest tests/unit/ -v
```

**Solution 2:** Use python -m:
```powershell
python -m pytest tests/unit/ -v
```

**Solution 3:** Set PYTHONPATH manually:
```powershell
$env:PYTHONPATH = "."
pytest tests/unit/ -v
```

### Issue: Tests Running but Failing

Check the error message carefully. Common issues:
- Database connection errors (should use in-memory SQLite)
- Missing fixtures
- Import errors

### Issue: No Tests Collected

Make sure:
- Test files start with `test_`
- Test functions start with `test_`
- You're in the correct directory

---

## Current Test Suite

### Unit Tests (64 tests)

| Service | File | Tests | Status |
|---------|------|-------|--------|
| Auth | `test_auth_service.py` | 24 | ✅ Passing |
| Entries | `test_entries_service.py` | 26 | ✅ Passing |
| Categories | `test_categories_service.py` | 14 | ✅ Passing |

### Integration Tests (17 stubs)

| API | File | Tests | Status |
|-----|------|-------|--------|
| Auth | `test_auth_api.py` | 17 | ⏳ In Progress |

---

## Test Results Interpretation

### Green/Passed
```
tests/unit/test_auth_service.py::TestCreateUser::test_create_user_success PASSED [100%]
```
✅ Test passed successfully

### Red/Failed
```
tests/unit/test_auth_service.py::TestCreateUser::test_create_user_success FAILED [100%]
```
❌ Test failed - check the error message

### Yellow/Skipped
```
tests/unit/test_auth_service.py::TestCreateUser::test_create_user_success SKIPPED [100%]
```
⚠️ Test was skipped (usually due to @pytest.mark.skip)

---

## Continuous Testing (Watch Mode)

For development, you can use pytest-watch to automatically re-run tests on file changes:

```powershell
# Install pytest-watch
pip install pytest-watch

# Watch and re-run tests
ptw tests/unit/ -- -v
```

---

## Best Practices

1. **Always run from project root:**
   ```powershell
   cd C:\Users\mhmts\PycharmProjects\expense-manager-web-app
   ```

2. **Run tests before committing:**
   ```powershell
   pytest tests/unit/ -v
   ```

3. **Check coverage regularly:**
   ```powershell
   pytest tests/unit/ --cov=app/services --cov-report=term-missing
   ```

4. **Use descriptive test names:**
   - Good: `test_create_user_with_duplicate_email_raises_error`
   - Bad: `test_user_creation`

5. **One assertion per test (when possible)**
   - Makes failures easier to debug

6. **Keep tests fast:**
   - Use in-memory database
   - Mock external services
   - Avoid unnecessary I/O

---

## Quick Reference Card

```powershell
# Most Common Commands
pytest tests/unit/ -v                           # Run all unit tests
pytest tests/unit/test_auth_service.py -v      # Run auth tests
pytest tests/unit/ --cov=app/services           # Run with coverage
pytest tests/unit/ -x                           # Stop on first failure
python -m pytest tests/unit/ -v                 # Alternative method

# Coverage
pytest --cov=app --cov-report=html              # HTML coverage report
pytest --cov=app --cov-report=term-missing      # Terminal coverage report

# Debugging
pytest tests/unit/ -vv                          # Very verbose
pytest tests/unit/ --tb=long                    # Full tracebacks
pytest tests/unit/ -s                           # Show print statements
pytest tests/unit/ --pdb                        # Drop into debugger on failure
```

---

## Need Help?

- **Full Documentation:** See `TESTING_IMPLEMENTATION_SUMMARY.md`
- **Test Examples:** Look at existing test files in `tests/unit/`
- **Pytest Documentation:** https://docs.pytest.org/
- **Coverage Documentation:** https://coverage.readthedocs.io/

---

**Last Updated:** November 17, 2025
