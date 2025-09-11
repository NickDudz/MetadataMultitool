"""
Privacy auditing functionality for Metadata Multitool.

This module provides tools to analyze image metadata for privacy risks
and generate detailed reports with remediation suggestions.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
import json
import re
from datetime import datetime
from enum import Enum

from .core import iter_images
from .exif import get_metadata_fields, has_exiftool, get_file_metadata
from .metadata_profiles import MetadataCategory, categorize_field


class RiskLevel(Enum):
    """Privacy risk levels."""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class PrivacyRisk:
    """Represents a privacy risk found in metadata."""
    field_name: str
    field_value: str
    risk_level: RiskLevel
    category: str
    description: str
    remediation: str
    file_path: Optional[str] = None


@dataclass
class FileAuditResult:
    """Audit results for a single file."""
    file_path: Path
    file_size: int
    risks: List[PrivacyRisk]
    metadata_count: int
    risk_score: float
    recommendations: List[str]


@dataclass
class AuditReport:
    """Complete privacy audit report."""
    summary: Dict[str, Any]
    file_results: List[FileAuditResult]
    overall_risks: List[PrivacyRisk]
    recommendations: List[str]
    scan_timestamp: datetime


# Risk patterns and rules
PRIVACY_RISK_RULES = {
    # GPS Location Data
    "GPS:GPSLatitude": {
        "risk_level": RiskLevel.CRITICAL,
        "category": "Location",
        "description": "Precise GPS coordinates reveal exact photo location",
        "remediation": "Remove GPS metadata before sharing to protect location privacy"
    },
    "GPS:GPSLongitude": {
        "risk_level": RiskLevel.CRITICAL,
        "category": "Location", 
        "description": "Precise GPS coordinates reveal exact photo location",
        "remediation": "Remove GPS metadata before sharing to protect location privacy"
    },
    "GPS:GPSAltitude": {
        "risk_level": RiskLevel.HIGH,
        "category": "Location",
        "description": "GPS altitude provides additional location specificity",
        "remediation": "Remove GPS metadata to eliminate location tracking"
    },
    
    # Personal Information
    "EXIF:CameraOwnerName": {
        "risk_level": RiskLevel.HIGH,
        "category": "Personal",
        "description": "Camera owner name reveals photographer identity",
        "remediation": "Remove or anonymize camera owner information"
    },
    "EXIF:Copyright": {
        "risk_level": RiskLevel.MEDIUM,
        "category": "Personal",
        "description": "Copyright field may contain personal information",
        "remediation": "Review copyright field for personal details"
    },
    "EXIF:Artist": {
        "risk_level": RiskLevel.MEDIUM,
        "category": "Personal",
        "description": "Artist field may reveal photographer identity",
        "remediation": "Consider removing or anonymizing artist information"
    },
    
    # Device Information
    "EXIF:Make": {
        "risk_level": RiskLevel.LOW,
        "category": "Device",
        "description": "Camera manufacturer can be used for device fingerprinting",
        "remediation": "Consider removing device information for anonymity"
    },
    "EXIF:Model": {
        "risk_level": RiskLevel.LOW,
        "category": "Device", 
        "description": "Camera model can be used for device fingerprinting",
        "remediation": "Consider removing device information for anonymity"
    },
    "EXIF:SerialNumber": {
        "risk_level": RiskLevel.HIGH,
        "category": "Device",
        "description": "Serial number uniquely identifies camera device",
        "remediation": "Remove serial number to prevent device tracking"
    },
    "EXIF:LensSerialNumber": {
        "risk_level": RiskLevel.HIGH,
        "category": "Device",
        "description": "Lens serial number can uniquely identify equipment",
        "remediation": "Remove lens serial number to prevent equipment tracking"
    },
    
    # Software Information
    "EXIF:Software": {
        "risk_level": RiskLevel.LOW,
        "category": "Software",
        "description": "Software information reveals editing tools and workflow",
        "remediation": "Consider removing software metadata for privacy"
    },
    "EXIF:ProcessingSoftware": {
        "risk_level": RiskLevel.LOW,
        "category": "Software",
        "description": "Processing software reveals post-production workflow",
        "remediation": "Remove software metadata to hide editing tools"
    },
    
    # Temporal Information
    "EXIF:DateTime": {
        "risk_level": RiskLevel.MEDIUM,
        "category": "Temporal",
        "description": "Creation timestamp can reveal when and where photos were taken",
        "remediation": "Consider removing or randomizing timestamps for privacy"
    },
    "EXIF:DateTimeOriginal": {
        "risk_level": RiskLevel.MEDIUM,
        "category": "Temporal",
        "description": "Original timestamp reveals when photo was actually taken",
        "remediation": "Remove or modify timestamps to prevent temporal tracking"
    },
    
    # Comments and Descriptions
    "EXIF:UserComment": {
        "risk_level": RiskLevel.HIGH,
        "category": "Personal",
        "description": "User comments may contain personal information or context",
        "remediation": "Review and remove user comments containing personal details"
    },
    "EXIF:ImageDescription": {
        "risk_level": RiskLevel.MEDIUM,
        "category": "Personal",
        "description": "Image descriptions may reveal context or personal information",
        "remediation": "Review image descriptions for sensitive content"
    },
    
    # IPTC Fields
    "IPTC:Keywords": {
        "risk_level": RiskLevel.MEDIUM,
        "category": "Content",
        "description": "Keywords may reveal image content and context",
        "remediation": "Review keywords for sensitive or identifying information"
    },
    "IPTC:Caption-Abstract": {
        "risk_level": RiskLevel.MEDIUM,
        "category": "Content",
        "description": "Captions may contain contextual or personal information",
        "remediation": "Review captions for privacy-sensitive content"
    },
    "IPTC:Byline": {
        "risk_level": RiskLevel.MEDIUM,
        "category": "Personal",
        "description": "Byline field may identify the photographer",
        "remediation": "Consider removing or anonymizing byline information"
    },
}


def analyze_field_value(field_name: str, field_value: str) -> List[PrivacyRisk]:
    """
    Analyze a metadata field value for privacy risks.
    
    Args:
        field_name: Name of the metadata field
        field_value: Value of the metadata field
        
    Returns:
        List of privacy risks found
    """
    risks = []
    
    # Check against known risky fields
    if field_name in PRIVACY_RISK_RULES:
        rule = PRIVACY_RISK_RULES[field_name]
        risk = PrivacyRisk(
            field_name=field_name,
            field_value=field_value,
            risk_level=rule["risk_level"],
            category=rule["category"],
            description=rule["description"],
            remediation=rule["remediation"]
        )
        risks.append(risk)
    
    # Pattern-based analysis for field values
    if field_value:
        # Check for email addresses
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', field_value):
            risks.append(PrivacyRisk(
                field_name=field_name,
                field_value=field_value,
                risk_level=RiskLevel.HIGH,
                category="Personal",
                description="Field contains email address",
                remediation="Remove or anonymize email addresses"
            ))
        
        # Check for phone numbers
        if re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', field_value):
            risks.append(PrivacyRisk(
                field_name=field_name,
                field_value=field_value,
                risk_level=RiskLevel.HIGH,
                category="Personal",
                description="Field contains phone number",
                remediation="Remove or anonymize phone numbers"
            ))
        
        # Check for URLs
        if re.search(r'https?://[^\s]+', field_value):
            risks.append(PrivacyRisk(
                field_name=field_name,
                field_value=field_value,
                risk_level=RiskLevel.MEDIUM,
                category="Personal",
                description="Field contains URL which may be identifying",
                remediation="Review URLs for privacy implications"
            ))
        
        # Check for potential names (simple heuristic)
        if field_name.lower() not in ['make', 'model', 'software'] and len(field_value.split()) >= 2:
            words = field_value.split()
            if all(word.istitle() for word in words if word.isalpha()):
                risks.append(PrivacyRisk(
                    field_name=field_name,
                    field_value=field_value,
                    risk_level=RiskLevel.MEDIUM,
                    category="Personal",
                    description="Field may contain personal name",
                    remediation="Review field for personal identifying information"
                ))
    
    return risks


def calculate_risk_score(risks: List[PrivacyRisk]) -> float:
    """
    Calculate overall privacy risk score for a set of risks.
    
    Args:
        risks: List of privacy risks
        
    Returns:
        Risk score from 0.0 (no risk) to 10.0 (maximum risk)
    """
    if not risks:
        return 0.0
    
    # Risk level weights
    weights = {
        RiskLevel.CRITICAL: 4.0,
        RiskLevel.HIGH: 3.0,
        RiskLevel.MEDIUM: 2.0,
        RiskLevel.LOW: 1.0,
        RiskLevel.INFO: 0.5
    }
    
    # Calculate weighted score
    total_weight = sum(weights[risk.risk_level] for risk in risks)
    
    # Normalize to 0-10 scale (assuming max ~20 risks of critical level)
    normalized_score = min(10.0, (total_weight / 80.0) * 10.0)
    
    return round(normalized_score, 1)


def audit_file(file_path: Path) -> FileAuditResult:
    """
    Perform privacy audit on a single image file.
    
    Args:
        file_path: Path to image file
        
    Returns:
        FileAuditResult with audit findings
    """
    risks = []
    recommendations = []
    
    try:
        # Get file size
        file_size = file_path.stat().st_size
        
        # Get metadata
        if has_exiftool():
            metadata = get_file_metadata(file_path)
        else:
            metadata = {}
            recommendations.append("Install ExifTool for comprehensive metadata analysis")
        
        metadata_count = len(metadata)
        
        # Analyze each metadata field
        for field_name, field_value in metadata.items():
            if field_value:
                field_risks = analyze_field_value(field_name, str(field_value))
                for risk in field_risks:
                    risk.file_path = str(file_path)
                risks.extend(field_risks)
        
        # Generate recommendations based on findings
        if any(risk.risk_level == RiskLevel.CRITICAL for risk in risks):
            recommendations.append("URGENT: Remove critical privacy data (GPS coordinates) before sharing")
        
        if any(risk.category == "Personal" for risk in risks):
            recommendations.append("Review and remove personal identifying information")
        
        if any(risk.category == "Device" for risk in risks):
            recommendations.append("Consider removing device fingerprinting data")
        
        if metadata_count > 20:
            recommendations.append("File contains extensive metadata - consider using 'remove_all' profile")
        elif metadata_count > 0:
            recommendations.append("Use selective cleaning to preserve useful metadata while removing private data")
        
        # Calculate risk score
        risk_score = calculate_risk_score(risks)
        
        return FileAuditResult(
            file_path=file_path,
            file_size=file_size,
            risks=risks,
            metadata_count=metadata_count,
            risk_score=risk_score,
            recommendations=recommendations
        )
        
    except Exception as e:
        # Return error result
        return FileAuditResult(
            file_path=file_path,
            file_size=file_path.stat().st_size if file_path.exists() else 0,
            risks=[PrivacyRisk(
                field_name="audit_error",
                field_value=str(e),
                risk_level=RiskLevel.INFO,
                category="Error",
                description=f"Error analyzing file: {e}",
                remediation="Check file accessibility and format"
            )],
            metadata_count=0,
            risk_score=0.0,
            recommendations=["Unable to analyze file - check file format and permissions"]
        )


def audit_directory(
    directory_path: Path,
    recursive: bool = False,
    max_files: Optional[int] = None
) -> AuditReport:
    """
    Perform privacy audit on all images in a directory.
    
    Args:
        directory_path: Directory to audit
        recursive: Whether to scan subdirectories
        max_files: Maximum number of files to scan (None for unlimited)
        
    Returns:
        AuditReport with comprehensive findings
    """
    # Find all images
    try:
        all_images = list(iter_images(directory_path, recursive=recursive))
    except Exception as e:
        # Return error report
        return AuditReport(
            summary={
                "error": f"Error scanning directory: {e}",
                "files_scanned": 0,
                "total_risks": 0
            },
            file_results=[],
            overall_risks=[],
            recommendations=["Check directory path and permissions"],
            scan_timestamp=datetime.now()
        )
    
    # Limit files if requested
    if max_files and len(all_images) > max_files:
        all_images = all_images[:max_files]
    
    # Audit each file
    file_results = []
    overall_risks = []
    
    for image_path in all_images:
        file_result = audit_file(image_path)
        file_results.append(file_result)
        overall_risks.extend(file_result.risks)
    
    # Generate summary statistics
    total_files = len(file_results)
    total_risks = len(overall_risks)
    
    risk_counts = {level: 0 for level in RiskLevel}
    for risk in overall_risks:
        risk_counts[risk.risk_level] += 1
    
    category_counts = {}
    for risk in overall_risks:
        category_counts[risk.category] = category_counts.get(risk.category, 0) + 1
    
    avg_risk_score = sum(result.risk_score for result in file_results) / max(1, total_files)
    high_risk_files = [result for result in file_results if result.risk_score >= 7.0]
    
    # Generate overall recommendations
    recommendations = []
    
    if risk_counts[RiskLevel.CRITICAL] > 0:
        recommendations.append(f"🚨 CRITICAL: {risk_counts[RiskLevel.CRITICAL]} files contain GPS coordinates - remove before sharing!")
    
    if risk_counts[RiskLevel.HIGH] > 0:
        recommendations.append(f"⚠️  HIGH RISK: {risk_counts[RiskLevel.HIGH]} high-risk privacy issues found")
    
    if category_counts.get("Personal", 0) > 0:
        recommendations.append(f"👤 Personal information found in {category_counts['Personal']} metadata fields")
    
    if category_counts.get("Device", 0) > 0:
        recommendations.append(f"📱 Device fingerprinting data found in {category_counts['Device']} fields")
    
    if len(high_risk_files) > 0:
        recommendations.append(f"🎯 {len(high_risk_files)} files have high privacy risk scores (≥7.0)")
    
    # Suggest appropriate cleaning profiles
    if risk_counts[RiskLevel.CRITICAL] > 0 or avg_risk_score > 6.0:
        recommendations.append("💡 Recommendation: Use 'remove_all' profile for maximum privacy")
    elif category_counts.get("Personal", 0) > 0 or category_counts.get("Device", 0) > 0:
        recommendations.append("💡 Recommendation: Use 'social_media' profile for safe sharing")
    elif total_risks > 0:
        recommendations.append("💡 Recommendation: Use 'remove_privacy' profile to keep technical data")
    else:
        recommendations.append("✅ Files appear to have minimal privacy risks")
    
    summary = {
        "files_scanned": total_files,
        "total_risks": total_risks,
        "average_risk_score": round(avg_risk_score, 1),
        "high_risk_files": len(high_risk_files),
        "risk_distribution": {level.value: count for level, count in risk_counts.items()},
        "category_distribution": category_counts,
        "directory": str(directory_path),
        "recursive": recursive
    }
    
    return AuditReport(
        summary=summary,
        file_results=file_results,
        overall_risks=overall_risks,
        recommendations=recommendations,
        scan_timestamp=datetime.now()
    )


def generate_html_report(audit_report: AuditReport, output_path: Path) -> None:
    """
    Generate an HTML privacy audit report.
    
    Args:
        audit_report: Audit report data
        output_path: Path to save HTML report
    """
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Audit Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .risk-critical {{ color: #dc3545; font-weight: bold; }}
        .risk-high {{ color: #fd7e14; font-weight: bold; }}
        .risk-medium {{ color: #ffc107; font-weight: bold; }}
        .risk-low {{ color: #28a745; }}
        .risk-info {{ color: #17a2b8; }}
        .recommendations {{ background: #e7f3ff; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .file-result {{ border: 1px solid #dee2e6; margin-bottom: 15px; padding: 15px; border-radius: 5px; }}
        .file-header {{ font-weight: bold; margin-bottom: 10px; }}
        .risk-item {{ margin: 5px 0; padding: 8px; background: #f8f9fa; border-radius: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        .score-high {{ background-color: #ffebee; }}
        .score-medium {{ background-color: #fff3e0; }}
        .score-low {{ background-color: #e8f5e8; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Privacy Audit Report</h1>
        <p>Generated on {audit_report.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Directory: <code>{audit_report.summary['directory']}</code></p>
    </div>
    
    <div class="summary">
        <h2>📊 Summary</h2>
        <p><strong>Files Scanned:</strong> {audit_report.summary['files_scanned']}</p>
        <p><strong>Total Privacy Risks:</strong> {audit_report.summary['total_risks']}</p>
        <p><strong>Average Risk Score:</strong> {audit_report.summary['average_risk_score']}/10</p>
        <p><strong>High Risk Files:</strong> {audit_report.summary['high_risk_files']}</p>
        
        <h3>Risk Distribution</h3>
        <ul>
"""
    
    # Add risk distribution
    for level, count in audit_report.summary['risk_distribution'].items():
        if count > 0:
            css_class = f"risk-{level}"
            html_content += f'<li class="{css_class}">{level.upper()}: {count} risks</li>\n'
    
    html_content += """
        </ul>
    </div>
    
    <div class="recommendations">
        <h2>💡 Recommendations</h2>
        <ul>
"""
    
    # Add recommendations
    for rec in audit_report.recommendations:
        html_content += f"<li>{rec}</li>\n"
    
    html_content += """
        </ul>
    </div>
    
    <h2>📁 File Analysis</h2>
    <table>
        <thead>
            <tr>
                <th>File</th>
                <th>Risk Score</th>
                <th>Metadata Count</th>
                <th>Top Risks</th>
            </tr>
        </thead>
        <tbody>
"""
    
    # Add file results
    for result in audit_report.file_results:
        score_class = "score-low"
        if result.risk_score >= 7.0:
            score_class = "score-high"
        elif result.risk_score >= 4.0:
            score_class = "score-medium"
        
        top_risks = [risk for risk in result.risks if risk.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]][:3]
        risk_summary = ", ".join([f"{risk.category}" for risk in top_risks]) or "None"
        
        html_content += f"""
            <tr class="{score_class}">
                <td>{result.file_path.name}</td>
                <td>{result.risk_score}/10</td>
                <td>{result.metadata_count}</td>
                <td>{risk_summary}</td>
            </tr>
        """
    
    html_content += """
        </tbody>
    </table>
    
    <h2>🔍 Detailed Findings</h2>
"""
    
    # Add detailed file results
    for result in audit_report.file_results:
        if result.risks:
            html_content += f"""
    <div class="file-result">
        <div class="file-header">{result.file_path.name} (Risk Score: {result.risk_score}/10)</div>
"""
            for risk in result.risks:
                css_class = f"risk-{risk.risk_level.value}"
                html_content += f"""
        <div class="risk-item">
            <span class="{css_class}">[{risk.risk_level.value.upper()}]</span>
            <strong>{risk.field_name}:</strong> {risk.description}
            <br><small>💡 {risk.remediation}</small>
        </div>
"""
            html_content += "</div>\n"
    
    html_content += """
    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 0.9em; color: #666;">
        <p>Generated by Metadata Multitool Privacy Auditor</p>
        <p>This report identifies potential privacy risks in image metadata. Review findings and use appropriate cleaning profiles before sharing images.</p>
    </footer>
</body>
</html>
"""
    
    output_path.write_text(html_content, encoding='utf-8')


def export_audit_json(audit_report: AuditReport, output_path: Path) -> None:
    """
    Export audit report as JSON for programmatic analysis.
    
    Args:
        audit_report: Audit report data
        output_path: Path to save JSON report
    """
    # Convert to JSON-serializable format
    json_data = {
        "scan_timestamp": audit_report.scan_timestamp.isoformat(),
        "summary": audit_report.summary,
        "recommendations": audit_report.recommendations,
        "file_results": [
            {
                "file_path": str(result.file_path),
                "file_size": result.file_size,
                "metadata_count": result.metadata_count,
                "risk_score": result.risk_score,
                "recommendations": result.recommendations,
                "risks": [
                    {
                        "field_name": risk.field_name,
                        "field_value": risk.field_value,
                        "risk_level": risk.risk_level.value,
                        "category": risk.category,
                        "description": risk.description,
                        "remediation": risk.remediation
                    }
                    for risk in result.risks
                ]
            }
            for result in audit_report.file_results
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        directory = Path(sys.argv[1])
        if directory.exists():
            print(f"Auditing directory: {directory}")
            report = audit_directory(directory)
            
            print(f"\nSummary:")
            print(f"Files scanned: {report.summary['files_scanned']}")
            print(f"Total risks: {report.summary['total_risks']}")
            print(f"Average risk score: {report.summary['average_risk_score']}/10")
            
            print(f"\nRecommendations:")
            for rec in report.recommendations:
                print(f"- {rec}")
            
            # Generate HTML report
            html_output = directory / "privacy_audit_report.html"
            generate_html_report(report, html_output)
            print(f"\nHTML report saved to: {html_output}")
        else:
            print(f"Directory not found: {directory}")
    else:
        print("Usage: python audit.py <directory_path>")