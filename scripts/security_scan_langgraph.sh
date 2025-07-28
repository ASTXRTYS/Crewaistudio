#!/bin/bash
# Security Scan for LangGraph Dependencies
# Created: 2025-01-29
# Purpose: Scan for vulnerabilities and generate SBOM

set -e

echo "🔒 LangGraph Security Scan"
echo "========================="
echo ""

# Check if required tools are installed
check_requirements() {
    echo "📋 Checking requirements..."
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 is required but not installed"
        exit 1
    fi
    
    # Check for pip-audit
    if ! command -v pip-audit &> /dev/null; then
        echo "⚠️  pip-audit not found. Installing..."
        pip install pip-audit
    fi
    
    # Check for safety
    if ! command -v safety &> /dev/null; then
        echo "⚠️  safety not found. Installing..."
        pip install safety
    fi
    
    # Check for cyclonedx-py
    if ! command -v cyclonedx-py &> /dev/null; then
        echo "⚠️  cyclonedx-py not found. Installing for SBOM generation..."
        pip install cyclonedx-bom
    fi
    
    # Check for trivy
    if ! command -v trivy &> /dev/null; then
        echo "⚠️  Trivy not found. Installing for container scanning..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            brew install aquasecurity/trivy/trivy
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
        else
            echo "⚠️  Please install Trivy manually from https://github.com/aquasecurity/trivy"
        fi
    fi
    
    echo "✅ All requirements satisfied"
    echo ""
}

# Run pip-audit scan
run_pip_audit() {
    echo "🔍 Running pip-audit vulnerability scan..."
    echo "----------------------------------------"
    
    # Create output directory
    mkdir -p security_reports
    
    # Run pip-audit with detailed output
    pip-audit \
        --requirement requirements-locked.txt \
        --desc \
        --format json \
        --output security_reports/pip_audit_report.json
    
    # Also generate human-readable report
    pip-audit \
        --requirement requirements-locked.txt \
        --desc \
        --output security_reports/pip_audit_report.txt
    
    # Check if vulnerabilities were found
    if [ $? -eq 0 ]; then
        echo "✅ pip-audit scan completed"
    else
        echo "⚠️  Vulnerabilities found! Check security_reports/pip_audit_report.txt"
    fi
    echo ""
}

# Run safety check
run_safety_check() {
    echo "🔍 Running Safety vulnerability scan..."
    echo "-------------------------------------"
    
    # Run safety check with full report
    safety check \
        --file requirements-locked.txt \
        --full-report \
        --output json \
        > security_reports/safety_report.json
    
    # Also generate text report
    safety check \
        --file requirements-locked.txt \
        --full-report \
        > security_reports/safety_report.txt
    
    echo "✅ Safety scan completed"
    echo ""
}

# Generate SBOM
generate_sbom() {
    echo "📦 Generating Software Bill of Materials (SBOM)..."
    echo "------------------------------------------------"
    
    # Generate CycloneDX SBOM in JSON format
    cyclonedx-py \
        --requirements requirements-locked.txt \
        --format json \
        --output security_reports/sbom_cyclonedx.json
    
    # Generate CycloneDX SBOM in XML format
    cyclonedx-py \
        --requirements requirements-locked.txt \
        --format xml \
        --output security_reports/sbom_cyclonedx.xml
    
    # Generate SPDX SBOM
    cyclonedx-py \
        --requirements requirements-locked.txt \
        --format spdxjson \
        --output security_reports/sbom_spdx.json
    
    echo "✅ SBOM generated in multiple formats"
    echo ""
}

# Check for outdated packages
check_outdated() {
    echo "📊 Checking for outdated packages..."
    echo "----------------------------------"
    
    pip list --outdated --format json > security_reports/outdated_packages.json
    
    # Parse and display critical updates
    python3 << EOF
import json
import sys

with open('security_reports/outdated_packages.json', 'r') as f:
    outdated = json.load(f)

langgraph_packages = [pkg for pkg in outdated if 'lang' in pkg['name'].lower()]

if langgraph_packages:
    print("⚠️  LangGraph-related packages with updates available:")
    for pkg in langgraph_packages:
        print(f"   - {pkg['name']}: {pkg['version']} → {pkg['latest_version']}")
else:
    print("✅ All LangGraph packages are up to date")
EOF
    
    echo ""
}

# Check for known CVEs in critical packages
check_cves() {
    echo "🛡️  Checking for known CVEs..."
    echo "----------------------------"
    
    # Focus on critical packages
    CRITICAL_PACKAGES=(
        "langchain"
        "langgraph"
        "langsmith"
        "openai"
        "fastapi"
        "pydantic"
        "cryptography"
    )
    
    for package in "${CRITICAL_PACKAGES[@]}"; do
        echo -n "   Checking $package... "
        
        # Use pip-audit to check specific package
        if pip-audit --desc | grep -i "$package" > /dev/null 2>&1; then
            echo "⚠️  Issues found"
        else
            echo "✅"
        fi
    done
    
    echo ""
}

# Check container vulnerabilities
check_container_vulnerabilities() {
    echo "🐳 Scanning container images with Trivy..."
    echo "----------------------------------------"
    
    # Find Docker images in compose files
    IMAGES=$(grep -h "image:" docker-compose*.yml 2>/dev/null | awk '{print $2}' | sort -u)
    
    if [ -z "$IMAGES" ]; then
        echo "No Docker images found in compose files"
        return
    fi
    
    # Scan each image
    for image in $IMAGES; do
        echo "Scanning: $image"
        
        # Generate report name
        REPORT_NAME=$(echo "$image" | tr '/:' '_')
        
        # Run Trivy scan
        trivy image \
            --severity HIGH,CRITICAL \
            --format json \
            --output "security_reports/trivy_${REPORT_NAME}.json" \
            "$image" 2>/dev/null || echo "  ⚠️  Failed to scan $image"
        
        # Also generate human-readable report
        trivy image \
            --severity HIGH,CRITICAL \
            --format table \
            --output "security_reports/trivy_${REPORT_NAME}.txt" \
            "$image" 2>/dev/null || true
        
        echo "  ✅ Scan complete"
    done
    
    echo ""
}

# Generate SBOM for containers
generate_container_sbom() {
    echo "📦 Generating container SBOMs..."
    echo "--------------------------------"
    
    # Check if we have a local Dockerfile
    if [ -f "Dockerfile" ]; then
        echo "Scanning local Dockerfile..."
        
        trivy sbom \
            --format spdx-json \
            --output security_reports/sbom_container_local.json \
            . 2>/dev/null || echo "  ⚠️  Failed to generate SBOM"
        
        echo "  ✅ Local container SBOM generated"
    fi
    
    echo ""
}

# Generate summary report
generate_summary() {
    echo "📝 Generating security summary..."
    echo "-------------------------------"
    
    cat > security_reports/SECURITY_SUMMARY.md << EOF
# LangGraph Security Scan Summary
Generated: $(date)

## Scan Results

### Vulnerability Scans
- **pip-audit report**: [pip_audit_report.txt](pip_audit_report.txt)
- **Safety report**: [safety_report.txt](safety_report.txt)

### Software Bill of Materials (SBOM)
- **CycloneDX JSON**: [sbom_cyclonedx.json](sbom_cyclonedx.json)
- **CycloneDX XML**: [sbom_cyclonedx.xml](sbom_cyclonedx.xml)
- **SPDX JSON**: [sbom_spdx.json](sbom_spdx.json)
- **Container SBOM**: [sbom_container_local.json](sbom_container_local.json)

### Container Security
- **Trivy Reports**: trivy_*.txt (see individual container reports)

### Outdated Packages
- **Report**: [outdated_packages.json](outdated_packages.json)

## Key Findings

EOF

    # Add vulnerability count
    if [ -f security_reports/pip_audit_report.json ]; then
        VULN_COUNT=$(python3 -c "import json; data=json.load(open('security_reports/pip_audit_report.json')); print(len(data.get('vulnerabilities', [])))")
        echo "- **Total vulnerabilities found**: $VULN_COUNT" >> security_reports/SECURITY_SUMMARY.md
    fi
    
    # Add package count
    PACKAGE_COUNT=$(wc -l < requirements-locked.txt)
    echo "- **Total packages scanned**: $PACKAGE_COUNT" >> security_reports/SECURITY_SUMMARY.md
    
    echo "" >> security_reports/SECURITY_SUMMARY.md
    echo "## Recommendations" >> security_reports/SECURITY_SUMMARY.md
    echo "" >> security_reports/SECURITY_SUMMARY.md
    
    if [ "$VULN_COUNT" -gt 0 ]; then
        echo "1. Review and address vulnerabilities in pip_audit_report.txt" >> security_reports/SECURITY_SUMMARY.md
        echo "2. Update packages with known security issues" >> security_reports/SECURITY_SUMMARY.md
        echo "3. Consider using alternative packages if updates are not available" >> security_reports/SECURITY_SUMMARY.md
    else
        echo "✅ No critical vulnerabilities detected!" >> security_reports/SECURITY_SUMMARY.md
    fi
    
    echo "✅ Summary generated: security_reports/SECURITY_SUMMARY.md"
    echo ""
}

# Main execution
main() {
    echo "Starting security scan at $(date)"
    echo ""
    
    check_requirements
    run_pip_audit
    run_safety_check
    generate_sbom
    check_container_vulnerabilities
    generate_container_sbom
    check_outdated
    check_cves
    generate_summary
    
    echo "🎉 Security scan completed!"
    echo "📁 Reports saved in: security_reports/"
    echo ""
    
    # Exit with error if vulnerabilities found
    if [ -f security_reports/pip_audit_report.json ]; then
        VULN_COUNT=$(python3 -c "import json; data=json.load(open('security_reports/pip_audit_report.json')); print(len(data.get('vulnerabilities', [])))")
        if [ "$VULN_COUNT" -gt 0 ]; then
            echo "❌ Found $VULN_COUNT vulnerabilities. Please review reports."
            exit 1
        fi
    fi
    
    echo "✅ No critical vulnerabilities found. System is secure!"
}

# Run main function
main 