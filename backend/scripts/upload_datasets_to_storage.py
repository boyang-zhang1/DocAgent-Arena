"""
One-time script to upload local datasets to Supabase Storage.

This uploads all dataset files from local disk to cloud storage.
After upload is verified, local files can be kept as backup (they're gitignored).

Usage:
    cd backend
    python scripts/upload_datasets_to_storage.py

    # Or upload specific dataset:
    python scripts/upload_datasets_to_storage.py --dataset squad2
    python scripts/upload_datasets_to_storage.py --dataset qasper
    python scripts/upload_datasets_to_storage.py --dataset policyqa
"""

import sys
from pathlib import Path
import argparse
import logging
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

from api.services.storage import SupabaseStorageService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def upload_squad(storage: SupabaseStorageService, data_dir: Path):
    """Upload SQuAD dataset files."""
    logger.info("=" * 60)
    logger.info("Uploading SQuAD dataset...")
    logger.info("=" * 60)

    # Get existing files in storage
    existing_files = set(storage.list_available())
    logger.info(f"Found {len(existing_files)} existing files in storage")

    squad_dir = data_dir / "datasets" / "SQuAD2"

    files_to_upload = [
        ("train-v2.0.json", "squad2/train-v2.0.json"),
        ("dev-v2.0.json", "squad2/dev-v2.0.json"),
    ]

    for local_filename, storage_path in files_to_upload:
        # Check if already exists
        if storage_path in existing_files:
            logger.info(f"⏭️  Skipping {local_filename} (already in storage)")
            continue

        local_path = squad_dir / local_filename

        if not local_path.exists():
            logger.warning(f"⚠️  File not found: {local_path}")
            continue

        file_size_mb = local_path.stat().st_size / (1024 * 1024)
        logger.info(f"📤 Uploading {local_filename} ({file_size_mb:.1f} MB)...")

        try:
            url = storage.upload(str(local_path), storage_path)
            logger.info(f"✅ Uploaded to: {storage_path}")
            logger.info(f"   URL: {url}")
        except Exception as e:
            logger.error(f"❌ Failed to upload {local_filename}: {e}")


def upload_qasper_cache(storage: SupabaseStorageService, data_dir: Path):
    """Upload Qasper parquet cache files."""
    logger.info("=" * 60)
    logger.info("Uploading Qasper parquet cache files...")
    logger.info("=" * 60)

    # Get existing files in storage
    existing_files = set(storage.list_available())
    logger.info(f"Found {len(existing_files)} existing files in storage")

    cache_dir = data_dir / "datasets" / "Qasper" / "cache"

    if not cache_dir.exists():
        logger.warning(f"⚠️  Qasper cache directory not found: {cache_dir}")
        logger.info(f"   Run a benchmark first to generate cache files")
        return

    parquet_files = list(cache_dir.glob("*.parquet"))
    logger.info(f"Found {len(parquet_files)} local parquet files")

    # Filter out already uploaded files
    to_upload = []
    skipped = 0
    for parquet_path in parquet_files:
        storage_path = f"qasper/cache/{parquet_path.name}"
        if storage_path in existing_files:
            skipped += 1
        else:
            to_upload.append(parquet_path)

    logger.info(f"📊 {len(to_upload)} new files to upload, {skipped} already in storage")

    for i, parquet_path in enumerate(to_upload, 1):
        file_size_mb = parquet_path.stat().st_size / (1024 * 1024)
        logger.info(f"📤 [{i}/{len(to_upload)}] Uploading {parquet_path.name} ({file_size_mb:.1f} MB)...")

        storage_path = f"qasper/cache/{parquet_path.name}"

        try:
            url = storage.upload(str(parquet_path), storage_path)
            logger.info(f"✅ Uploaded to: {storage_path}")
            logger.info(f"   URL: {url}")
        except Exception as e:
            logger.error(f"❌ Failed to upload {parquet_path.name}: {e}")


def upload_qasper(storage: SupabaseStorageService, data_dir: Path):
    """Upload Qasper PDF files."""
    logger.info("=" * 60)
    logger.info("Uploading Qasper PDFs...")
    logger.info("=" * 60)

    # Get existing files in storage
    existing_files = set(storage.list_available())

    pdf_dir = data_dir / "datasets" / "Qasper" / "pdfs"

    if not pdf_dir.exists():
        logger.warning(f"⚠️  Qasper PDF directory not found: {pdf_dir}")
        return

    pdf_files = list(pdf_dir.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} local PDF files")

    # Filter out already uploaded files
    to_upload = []
    skipped = 0
    for pdf_path in pdf_files:
        storage_path = f"qasper/pdfs/{pdf_path.name}"
        if storage_path in existing_files:
            skipped += 1
        else:
            to_upload.append(pdf_path)

    logger.info(f"📊 {len(to_upload)} new files to upload, {skipped} already in storage")

    for i, pdf_path in enumerate(to_upload, 1):
        file_size_kb = pdf_path.stat().st_size / 1024
        logger.info(f"📤 [{i}/{len(to_upload)}] Uploading {pdf_path.name} ({file_size_kb:.1f} KB)...")

        storage_path = f"qasper/pdfs/{pdf_path.name}"

        try:
            url = storage.upload(str(pdf_path), storage_path)
            logger.info(f"✅ Uploaded to: {storage_path}")
        except Exception as e:
            logger.error(f"❌ Failed to upload {pdf_path.name}: {e}")


def upload_policyqa_json(storage: SupabaseStorageService, data_dir: Path):
    """Upload PolicyQA Q&A JSON files."""
    logger.info("=" * 60)
    logger.info("Uploading PolicyQA Q&A JSON files...")
    logger.info("=" * 60)

    # Get existing files in storage
    existing_files = set(storage.list_available())
    logger.info(f"Found {len(existing_files)} existing files in storage")

    policyqa_dir = data_dir / "datasets" / "PolicyQA"

    files_to_upload = [
        ("train.json", "policyqa/train.json"),
        ("dev.json", "policyqa/dev.json"),
        ("test.json", "policyqa/test.json"),
    ]

    for local_filename, storage_path in files_to_upload:
        # Check if already exists
        if storage_path in existing_files:
            logger.info(f"⏭️  Skipping {local_filename} (already in storage)")
            continue

        local_path = policyqa_dir / local_filename

        if not local_path.exists():
            logger.warning(f"⚠️  File not found: {local_path}")
            continue

        file_size_mb = local_path.stat().st_size / (1024 * 1024)
        logger.info(f"📤 Uploading {local_filename} ({file_size_mb:.1f} MB)...")

        try:
            url = storage.upload(str(local_path), storage_path)
            logger.info(f"✅ Uploaded to: {storage_path}")
            logger.info(f"   URL: {url}")
        except Exception as e:
            logger.error(f"❌ Failed to upload {local_filename}: {e}")


def upload_policyqa(storage: SupabaseStorageService, data_dir: Path):
    """Upload PolicyQA PDF files."""
    logger.info("=" * 60)
    logger.info("Uploading PolicyQA PDFs...")
    logger.info("=" * 60)

    # Get existing files in storage
    existing_files = set(storage.list_available())

    pdf_dir = data_dir / "datasets" / "PolicyQA" / "pdfs"

    if not pdf_dir.exists():
        logger.warning(f"⚠️  PolicyQA PDF directory not found: {pdf_dir}")
        logger.info(f"   You may need to run the preprocessor first to generate PDFs")
        return

    pdf_files = list(pdf_dir.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} local PDF files")

    # Filter out already uploaded files
    to_upload = []
    skipped = 0
    for pdf_path in pdf_files:
        storage_path = f"policyqa/pdfs/{pdf_path.name}"
        if storage_path in existing_files:
            skipped += 1
        else:
            to_upload.append(pdf_path)

    logger.info(f"📊 {len(to_upload)} new files to upload, {skipped} already in storage")

    for i, pdf_path in enumerate(to_upload, 1):
        file_size_kb = pdf_path.stat().st_size / 1024
        logger.info(f"📤 [{i}/{len(to_upload)}] Uploading {pdf_path.name} ({file_size_kb:.1f} KB)...")

        storage_path = f"policyqa/pdfs/{pdf_path.name}"

        try:
            url = storage.upload(str(pdf_path), storage_path)
            logger.info(f"✅ Uploaded to: {storage_path}")
        except Exception as e:
            logger.error(f"❌ Failed to upload {pdf_path.name}: {e}")


def verify_uploads(storage: SupabaseStorageService):
    """Verify all uploads completed successfully."""
    logger.info("=" * 60)
    logger.info("Verifying uploads...")
    logger.info("=" * 60)

    try:
        all_files = storage.list_available()
        logger.info(f"\n📊 Total files in storage: {len(all_files)}")

        # Group by dataset
        by_dataset = {}
        for path in all_files:
            dataset = path.split('/')[0]
            if dataset not in by_dataset:
                by_dataset[dataset] = []
            by_dataset[dataset].append(path)

        for dataset, files in sorted(by_dataset.items()):
            logger.info(f"\n{dataset}:")
            for f in sorted(files):
                logger.info(f"  ✓ {f}")

    except Exception as e:
        logger.error(f"❌ Failed to list files: {e}")


def main():
    parser = argparse.ArgumentParser(description="Upload datasets to Supabase Storage")
    parser.add_argument(
        '--dataset',
        choices=['squad2', 'qasper', 'qasper-cache', 'policyqa', 'policyqa-json', 'all'],
        default='all',
        help='Which dataset to upload (default: all)'
    )
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path(__file__).parent.parent.parent / "data",
        help='Path to data directory (default: ../data)'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify existing uploads, do not upload new files'
    )

    args = parser.parse_args()

    # Initialize storage service
    try:
        logger.info("Initializing Supabase Storage service...")
        storage = SupabaseStorageService()
        logger.info("✅ Connected to Supabase Storage")
    except Exception as e:
        logger.error(f"❌ Failed to initialize storage service: {e}")
        logger.error("   Make sure SUPABASE_URL and SUPABASE_SERVICE_KEY are set in .env")
        return 1

    if args.verify_only:
        verify_uploads(storage)
        return 0

    # Upload datasets
    if args.dataset in ['squad2', 'all']:
        upload_squad(storage, args.data_dir)

    if args.dataset in ['qasper', 'all']:
        upload_qasper(storage, args.data_dir)

    if args.dataset in ['qasper-cache', 'all']:
        upload_qasper_cache(storage, args.data_dir)

    if args.dataset in ['policyqa', 'all']:
        upload_policyqa(storage, args.data_dir)

    if args.dataset in ['policyqa-json', 'all']:
        upload_policyqa_json(storage, args.data_dir)

    # Verify uploads
    logger.info("\n")
    verify_uploads(storage)

    logger.info("\n" + "=" * 60)
    logger.info("✅ Upload complete!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("  1. Verify all files uploaded correctly (see list above)")
    logger.info("  2. Test loaders can fetch from storage:")
    logger.info("     python -c \"from src.datasets.loader import DatasetLoader; DatasetLoader.load_squad(storage_path='squad2/dev-v2.0.json', max_samples=2)\"")
    logger.info("  3. Keep local files as backup (they're gitignored)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
