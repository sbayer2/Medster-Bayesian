#!/usr/bin/env python3
"""
Test script to verify DICOM image loading works with GPT-4.1 vision.
"""
import sys
sys.path.insert(0, '/Users/sbm4_mac/Desktop/MDB/src')

from medster.tools.analysis.primitives import (
    scan_dicom_directory,
    load_dicom_image,
    analyze_image_with_claude
)

def test_dicom_vision():
    """Test DICOM loading and vision analysis."""

    # Step 1: Get first DICOM file
    print("Step 1: Scanning DICOM directory...")
    dicom_files = scan_dicom_directory()
    if not dicom_files:
        print("❌ No DICOM files found")
        return

    first_file = dicom_files[0]
    print(f"✅ Found {len(dicom_files)} DICOM files")
    print(f"   First file: {first_file}")

    # Step 2: Extract patient ID from filename (CORRECT METHOD)
    print("\nStep 2: Extracting patient ID from filename...")
    filename = first_file.split('/')[-1]  # Get just the filename
    print(f"   Filename: {filename}")

    # Parse: FirstName_LastName_UUID[REST].dcm
    # Try multiple parsing strategies
    parts = filename.split('_')
    if len(parts) >= 3:
        # Strategy 1: First+Last name (works for Coherent dataset)
        patient_id = f"{parts[0]}_{parts[1]}"
        print(f"   Strategy 1 (Name): {patient_id}")

        # Strategy 2: Extract UUID portion (between 2nd _ and first digit after UUID)
        uuid_part = parts[2].split('[')[0] if '[' in parts[2] else parts[2].split('1.')[0]
        print(f"   Strategy 2 (UUID): {uuid_part}")
    else:
        print("❌ Unexpected filename format")
        return

    # Step 3: Try loading with Strategy 1 (Name-based)
    print(f"\nStep 3: Loading DICOM image with patient_id='{patient_id}'...")
    image = load_dicom_image(patient_id, 0)

    if not image:
        print(f"❌ Failed to load with Strategy 1")

        # Try Strategy 2 (UUID-based)
        print(f"   Trying Strategy 2 with UUID '{uuid_part}'...")
        image = load_dicom_image(uuid_part, 0)

    if not image:
        print("❌ Failed to load DICOM image with both strategies")
        return

    print(f"✅ Successfully loaded image ({len(image)} chars base64)")

    # Step 4: Test vision analysis
    print("\nStep 4: Analyzing image with configured vision model...")
    print("   (Using VISION_MODEL from .env)")

    analysis = analyze_image_with_claude(
        image,
        "Analyze this brain CT image. Identify key anatomical structures visible and any abnormalities."
    )

    if "error" in analysis.lower() and "vision" in analysis.lower():
        print(f"❌ Vision analysis failed: {analysis[:200]}")
        return

    print(f"✅ Vision analysis completed!")
    print(f"\nAnalysis Result:\n{'-'*60}")
    print(analysis)
    print(f"{'-'*60}")

    return True

if __name__ == "__main__":
    try:
        success = test_dicom_vision()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
