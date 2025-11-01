# 🚀 Quick Start Guide

This guide will get you up and running in 5 minutes!

## Prerequisites

- Python 3.12 installed
- Docker (for the banking server) OR Java 17+

## Step-by-Step Setup

### Step 1: Navigate to Project

```bash
cd submissions/AnonymityAdvoc8
```

### Step 2: Complete Setup (One Command!)

Choose one of these methods:

**Option A: Automated Script** (Easiest)
```bash
./setup.sh
```

**Option B: Using Make** (Recommended)
```bash
make setup
```

**Option C: Manual**
```bash
python3.12 -m venv venv
source venv/bin/activate
pip3.12 install -r requirements-dev.txt
```

### Step 3: Start Banking Server

In a **separate terminal**:

```bash
# Using Docker (recommended)
docker run -d -p 8123:8123 singhacksbjb/sidequest-server:latest

# OR using Java
cd ../../server
java -jar core-banking-api.jar
```

Verify it's running:
```bash
curl http://localhost:8123/accounts/validate/ACC1000
```

### Step 4: Run the Client!

#### Test with Make:

```bash
# Run demo (shows all features)
make demo

# Transfer money
make run ARGS='transfer --from ACC1000 --to ACC1001 --amount 100'

# Validate account
make run ARGS='validate --account ACC1000'

# List accounts
make run ARGS='list'
```

#### Or activate venv and use Python:

```bash
source venv/bin/activate

python main.py transfer --from ACC1000 --to ACC1001 --amount 100
python main.py validate --account ACC1000
python main.py list
python example_usage.py
```

### Step 5: Run Tests

```bash
# All tests
make test

# With coverage report
make coverage

# Unit tests only (no server needed)
make test-unit
```

## Common Commands Reference

### Setup & Installation
```bash
make setup          # Complete setup (venv + install)
make venv           # Create virtual environment only
make install        # Install production dependencies
make install-dev    # Install dev dependencies
```

### Running the Client
```bash
make demo                                                    # Run example demo
make run ARGS='transfer --from ACC1000 --to ACC1001 --amount 100'  # Transfer
make run ARGS='validate --account ACC1000'                  # Validate
make run ARGS='balance --account ACC1000'                   # Balance
make run ARGS='list'                                        # List accounts
```

### Testing
```bash
make test              # Run all tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make coverage          # Tests with coverage report
```

### Code Quality
```bash
make format      # Format code with black
make lint        # Lint with ruff
make type-check  # Type check with mypy
```

### Cleanup
```bash
make clean       # Clean generated files
make clean-all   # Clean everything including venv
```

### Help
```bash
make help        # Show all available commands
make examples    # Show example commands
```

## Troubleshooting

### "python3.12 not found"

**macOS:**
```bash
brew install python@3.12
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv
```

**Or download from:** https://www.python.org/downloads/

### "Virtual environment not found"

```bash
make setup  # This will create it
# or
python3.12 -m venv venv
```

### "Server connection refused"

Make sure the banking server is running:
```bash
docker run -d -p 8123:8123 singhacksbjb/sidequest-server:latest
curl http://localhost:8123/accounts/validate/ACC1000
```

### Tests fail with "SKIP_INTEGRATION_TESTS"

Integration tests need the server running. To skip them:
```bash
export SKIP_INTEGRATION_TESTS=1
make test
```

## What's Next?

1. **Read the full README**: `readme.md`
2. **Check the code**: Explore `banking_client/` directory
3. **Review tests**: Look at `tests/` directory
4. **See submission details**: `SUBMISSION.md`

## Example Session

Here's what a complete session looks like:

```bash
# 1. Setup (one time only)
cd submissions/AnonymityAdvoc8
make setup

# 2. Start server (separate terminal)
docker run -d -p 8123:8123 singhacksbjb/sidequest-server:latest

# 3. Run client
make demo

# 4. Test it
make test

# 5. Try some transfers
make run ARGS='transfer --from ACC1000 --to ACC1001 --amount 100'
make run ARGS='validate --account ACC1000'
make run ARGS='list'

# 6. Check coverage
make coverage
```

That's it! You're ready to go! 🎉

For more details, see `readme.md` or run `make help`.

