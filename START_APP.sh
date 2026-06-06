#!/bin/bash
clear
echo ""
echo " ====================================================="
echo "  QS MARKETPLACE — Starting up..."
echo " ====================================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo " [ERROR] Python 3 is not installed."
    echo " Install it from: https://www.python.org/downloads/"
    read -p " Press Enter to exit..."
    exit 1
fi

echo " [OK] Python found: $(python3 --version)"

# Install dependencies
echo " [..] Installing/checking dependencies..."
pip3 install -r requirements.txt --quiet
echo " [OK] Dependencies ready."
echo ""
echo " ====================================================="
echo "  Server: http://127.0.0.1:5000"
echo "  Admin : admin@qsmarket.com / Admin@123"
echo "  Press CTRL+C to stop."
echo " ====================================================="
echo ""

python3 app.py
