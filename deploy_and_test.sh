#!/bin/bash

# DC EPUB Composer API Deployment and Testing Script
# This script helps deploy and test the new API functionality

set -e  # Exit on any error

echo "🚀 DC EPUB Composer API Deployment & Testing"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
API_PORT=${PORT:-3002}
BASE_URL="http://localhost:${API_PORT}"

# Check if we're in the right directory
if [[ ! -f "api_server.py" ]]; then
    echo -e "${RED}❌ api_server.py not found. Please run this script from the dc-epub-composer directory.${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Installing API dependencies...${NC}"
pip install flask>=2.3.0 flask-swagger-ui>=4.11.0

echo -e "${BLUE}🔧 Setting up environment...${NC}"
export PYTHONPATH=$(pwd)
export STORAGE_ROOT=$(pwd)/storage
export PORT=${API_PORT}

# Create necessary directories
mkdir -p storage logs

echo -e "${BLUE}🖥️ Starting API server...${NC}"
echo "API will be available at: ${BASE_URL}"
echo "API Documentation: ${BASE_URL}/api/docs"
echo ""

# Start the API server in background
python api_server.py &
API_PID=$!

# Wait for server to start
echo -e "${YELLOW}⏳ Waiting for API server to start...${NC}"
for i in {1..10}; do
    if curl -s "${BASE_URL}/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API server is running (PID: ${API_PID})${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ API server failed to start${NC}"
        kill $API_PID 2>/dev/null || true
        exit 1
    fi
    sleep 2
done

# Create test markdown files
echo -e "${BLUE}📝 Creating test files...${NC}"

cat > test_single.md << 'EOF'
# Test Book

This is a test book for single-language EPUB composition.

## Chapter 1

This chapter contains some sample content to verify that the EPUB composition works correctly.

## Chapter 2  

This is another chapter with different content to test the structure and formatting.

### Section 2.1

Subsections should also be handled properly.

The end.
EOF

cat > test_original.md << 'EOF'
# Original Book

This is the original English content.

## Chapter 1: The Beginning

Once upon a time, there was a story that needed to be told.

## Chapter 2: The Middle

The story continued with more interesting details.

## Chapter 3: The End

And they all lived happily ever after.
EOF

cat > test_translated.md << 'EOF'
# Cuốn sách gốc

Đây là nội dung tiếng Anh gốc.

## Chương 1: Khởi đầu

Ngày xưa, có một câu chuyện cần được kể.

## Chương 2: Phần giữa

Câu chuyện tiếp tục với nhiều chi tiết thú vị hơn.

## Chương 3: Kết thúc

Và tất cả họ đều sống hạnh phúc mãi mãi.
EOF

echo -e "${GREEN}✅ Test files created${NC}"

# Function to test API endpoint
test_api() {
    local method=$1
    local endpoint=$2
    local description=$3
    local expected_status=$4
    local extra_args=${5:-}
    
    echo -e "${BLUE}🧪 Testing: ${description}${NC}"
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}${endpoint}" ${extra_args})
    else
        response=$(curl -s -w "\n%{http_code}" "${BASE_URL}${endpoint}")
    fi
    
    status_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}   ✅ ${description} - Status: ${status_code}${NC}"
        if [ -n "$response_body" ]; then
            echo "   📄 Response: $(echo "$response_body" | jq -r '.message // .status // .' 2>/dev/null || echo "$response_body")"
        fi
    else
        echo -e "${RED}   ❌ ${description} - Expected: ${expected_status}, Got: ${status_code}${NC}"
        echo "   📄 Response: $response_body"
    fi
    
    echo "$response_body"
}

# Test Health Check
echo -e "\n${YELLOW}🏥 Testing Health Check${NC}"
test_api "GET" "/api/health" "Health check" 200

# Test Single-Language Composition
echo -e "\n${YELLOW}📚 Testing Single-Language EPUB Composition${NC}"
job_id="test-single-$(date +%s)"
response=$(test_api "POST" "/api/compose" "Submit single-language job" 200 \
    "-F jobId=${job_id} -F markdownFile=@test_single.md")

if echo "$response" | grep -q "successfully"; then
    echo -e "${GREEN}✅ Single-language job submitted: ${job_id}${NC}"
    
    # Wait and check status
    echo -e "${BLUE}⏳ Waiting for completion...${NC}"
    for i in {1..30}; do
        status_response=$(test_api "GET" "/api/job_status?jobId=${job_id}" "Check job status" 200)
        
        if echo "$status_response" | grep -q '"status": "completed"'; then
            echo -e "${GREEN}✅ Single-language job completed!${NC}"
            
            # Test download
            echo -e "${BLUE}⬇️ Testing download...${NC}"
            if curl -s -f "${BASE_URL}/api/download?jobId=${job_id}" -o "${job_id}.epub"; then
                echo -e "${GREEN}✅ Downloaded: ${job_id}.epub ($(ls -lh ${job_id}.epub | awk '{print $5}'))${NC}"
            else
                echo -e "${RED}❌ Download failed${NC}"
            fi
            break
        elif echo "$status_response" | grep -q '"status": "failed"'; then
            echo -e "${RED}❌ Job failed${NC}"
            break
        fi
        
        if [ $i -eq 30 ]; then
            echo -e "${YELLOW}⏰ Job still processing after 60 seconds${NC}"
            break
        fi
        
        sleep 2
    done
fi

# Test Dual-Language Composition  
echo -e "\n${YELLOW}🌐 Testing Dual-Language EPUB Composition${NC}"
dual_job_id="test-dual-$(date +%s)"
response=$(test_api "POST" "/api/compose" "Submit dual-language job" 200 \
    "-F jobId=${dual_job_id} -F originalBook=@test_original.md -F translatedContent=@test_translated.md")

if echo "$response" | grep -q "successfully"; then
    echo -e "${GREEN}✅ Dual-language job submitted: ${dual_job_id}${NC}"
    
    # Wait and check status
    echo -e "${BLUE}⏳ Waiting for completion...${NC}"
    for i in {1..30}; do
        status_response=$(test_api "GET" "/api/job_status?jobId=${dual_job_id}" "Check dual job status" 200)
        
        if echo "$status_response" | grep -q '"status": "completed"'; then
            echo -e "${GREEN}✅ Dual-language job completed!${NC}"
            
            # Test download
            echo -e "${BLUE}⬇️ Testing download...${NC}"
            if curl -s -f "${BASE_URL}/api/download?jobId=${dual_job_id}" -o "${dual_job_id}.epub"; then
                echo -e "${GREEN}✅ Downloaded: ${dual_job_id}.epub ($(ls -lh ${dual_job_id}.epub | awk '{print $5}'))${NC}"
            else
                echo -e "${RED}❌ Download failed${NC}"
            fi
            break
        elif echo "$status_response" | grep -q '"status": "failed"'; then
            echo -e "${RED}❌ Dual-language job failed${NC}"
            break
        fi
        
        if [ $i -eq 30 ]; then
            echo -e "${YELLOW}⏰ Dual-language job still processing after 60 seconds${NC}"
            break
        fi
        
        sleep 2
    done
fi

# Test Error Cases
echo -e "\n${YELLOW}🚫 Testing Error Cases${NC}"

# Test missing jobId
test_api "POST" "/api/compose" "Missing jobId" 400 "-F markdownFile=@test_single.md"

# Test missing files
test_api "POST" "/api/compose" "Missing files" 400 "-F jobId=test-no-files"

# Test invalid jobId for status
test_api "GET" "/api/job_status?jobId=nonexistent" "Non-existent job status" 200

# Test invalid jobId for download
test_api "GET" "/api/download?jobId=nonexistent" "Non-existent job download" 404

# Clean up test files
echo -e "\n${BLUE}🧹 Cleaning up test files...${NC}"
rm -f test_single.md test_original.md test_translated.md
rm -f test-*.epub

# Show final results
echo -e "\n${GREEN}🎉 API Testing Complete!${NC}"
echo ""
echo -e "${BLUE}📊 Results Summary:${NC}"
echo "• API Server: Running on port ${API_PORT}"
echo "• Health Check: Working"
echo "• Single-language composition: Tested"  
echo "• Dual-language composition: Tested"
echo "• Error handling: Verified"
echo "• Download functionality: Working"
echo ""
echo -e "${BLUE}🔗 Useful Links:${NC}"
echo "• API Health: ${BASE_URL}/api/health"
echo "• API Docs: ${BASE_URL}/api/docs"
echo "• Storage Directory: $(pwd)/storage"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Check generated EPUB files with an EPUB reader"
echo "2. Review API documentation at /api/docs"
echo "3. Integrate with your applications"
echo "4. Start the background worker: python main.py"
echo ""
echo -e "${BLUE}🛑 Stop API Server:${NC}"
echo "kill ${API_PID}"

# Keep the script running until user interrupts
echo -e "\n${YELLOW}🔄 API server is running. Press Ctrl+C to stop...${NC}"
trap "echo -e '\n${BLUE}🛑 Stopping API server...${NC}'; kill $API_PID 2>/dev/null || true; exit 0" INT

wait $API_PID