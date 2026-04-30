#!/bin/bash

# --- BOLD & COLOR FORMATTING ---
BOLD='\033[1m'
GREEN='\033[1;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}${CYAN}[ YUKI BOT AUTO-SETUP STARTED ]${NC}"
echo "------------------------------------------------"

# 1. READ PYTHON VERSION FROM RUNTIME.TXT
if [ -f "runtime.txt" ]; then
    PY_VER_FULL=$(cat runtime.txt | tr -d '\r' | tr -d ' ')
    # Extracting exact version (e.g., from python-3.11.4 to 3.11)
    PY_VER=$(echo $PY_VER_FULL | grep -oP '\d+\.\d+' | head -1)
    echo -e "${BOLD}${GREEN}[ DETECTED PYTHON VERSION: $PY_VER ]${NC}"
else
    PY_VER="3.11"
    echo -e "${BOLD}${YELLOW}[ RUNTIME.TXT NOT FOUND. USING DEFAULT: $PY_VER ]${NC}"
fi

# 2. INSTALL SYSTEM DEPENDENCIES
echo -e "\n${BOLD}${CYAN}[ INSTALLING SYSTEM DEPENDENCIES & PYTHON ]${NC}"
sudo apt update -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update -y
sudo apt install python$PY_VER python$PY_VER-venv python3-pip npm ffmpeg -y

# 3. CREATE AND ACTIVATE VIRTUAL ENVIRONMENT
echo -e "\n${BOLD}${CYAN}[ SETTING UP VIRTUAL ENVIRONMENT ]${NC}"
python$PY_VER -m venv venv
source venv/bin/activate
pip install -U pip

# 4. INSTALL REQUIREMENTS
echo -e "\n${BOLD}${CYAN}[ INSTALLING REQUIREMENTS.TXT ]${NC}"
pip install -r requirements.txt

# 5. ENVIRONMENT FILE SETUP (.ENV)
echo -e "\n------------------------------------------------"
echo -e "${BOLD}${CYAN}[ ENVIRONMENT VARIABLES (.ENV) SETUP ]${NC}"

if [ -f "sample.env" ]; then
    echo "Choose an option for .env setup:"
    echo "1) Fill variables step-by-step in terminal (Recommended)"
    echo "2) Open in Nano editor to paste everything manually"
    echo "3) Skip (I already have a .env file)"
    read -p "Enter your choice (1/2/3): " env_choice

    if [[ -z "$env_choice" || "$env_choice" == "1" ]]; then
        echo -e "\n${BOLD}Please enter the values. Leave blank to use the default value.${NC}"
        > .env # Create empty .env file
        
        while IFS='=' read -r key default_val; do
            # Skip comments and empty lines
            if [[ -n "$key" && "$key" != \#* ]]; then
                read -p "$key (Default: $default_val): " user_val
                if [[ -z "$user_val" ]]; then
                    echo "$key=$default_val" >> .env
                else
                    echo "$key=$user_val" >> .env
                fi
            fi
        done < sample.env
        echo -e "${BOLD}${GREEN}[ .ENV FILE CREATED SUCCESSFULLY ]${NC}"

    elif [[ "$env_choice" == "2" ]]; then
        cp sample.env .env
        echo -e "${BOLD}Opening Nano... Press Ctrl+X, then Y, then Enter to save.${NC}"
        sleep 2
        nano .env
    else
        echo -e "${BOLD}${YELLOW}[ SKIPPED .ENV SETUP ]${NC}"
    fi
else
    echo -e "${BOLD}${RED}[ WARNING: sample.env NOT FOUND! ]${NC}"
fi

# 6. INSTALL PM2
echo -e "\n------------------------------------------------"
echo -e "${BOLD}${CYAN}[ INSTALLING PM2 ]${NC}"
sudo npm install -g pm2

# 7. DEPLOY THE BOT
echo -e "\n${BOLD}${CYAN}[ DEPLOYING YUKI BOT ]${NC}"
# Passing module name as argument to the python executable in venv
pm2 start "venv/bin/python3" --name "YukiBot1" -- -m anikamusic
pm2 save

# 8. DISPLAY LOGS
echo -e "\n------------------------------------------------"
echo -e "${BOLD}${GREEN}[ SETUP COMPLETE AND BOT IS RUNNING! ]${NC}"
echo -e "${BOLD}Starting live logs... (Press Ctrl+C to exit logs)${NC}"
sleep 3
pm2 logs YukiBot

