# ECG Digitization API

A production-oriented FastAPI backend for converting ECG images into machine-readable ECG waveform data using the Open-ECG-Digitizer inference engine.

The API accepts an ECG image, validates and stores the original file, sends it to a dedicated ECG digitization worker, and exposes the generated waveform CSV, digital ECG image, metadata, and processing status through REST APIs.

---

## Overview

Traditional ECG records are often available as images rather than structured signal data.

This project provides a backend pipeline that converts an ECG image into structured waveform data.

### Pipeline

ECG Image
    ↓
FastAPI API
    ↓
File Validation
    ↓
Original Image Storage
    ↓
ECG Processing Worker
    ↓
Open-ECG-Digitizer
    ↓
Waveform Extraction
    ↓
CSV + Digital ECG Image + Metadata

---

## Features

- ECG image upload through REST API
- JPEG and PNG validation
- File size validation
- Actual image verification using Pillow
- Unique ECG ID generation
- Original ECG image preservation
- Integration with Open-ECG-Digitizer
- Dedicated digitizer worker process
- Separate Python environment for ML inference
- ECG waveform CSV generation
- Digital ECG image generation
- Metadata generation
- Processing lifecycle tracking
- Worker startup and graceful shutdown
- Worker crash detection
- Broken-pipe handling
- Worker timeout handling
- Force termination of unhealthy workers
- Partial processing cleanup
- Structured logging
- REST endpoints for generated outputs

---

## Architecture

```text
                    ┌──────────────────────┐
                    │      Client          │
                    │  Postman / Frontend  │
                    └──────────┬───────────┘
                               │
                               │ POST ECG Image
                               ▼
                    ┌──────────────────────┐
                    │     FastAPI API      │
                    │      /api/v1/ecg     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ File Validation      │
                    │ Service              │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    ECG Service       │
                    │ Business Logic       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Digitizer Service    │
                    │ Worker Manager       │
                    └──────────┬───────────┘
                               │
                         JSON over
                       stdin/stdout
                               │
                               ▼
              ┌─────────────────────────────────┐
              │     Open-ECG-Digitizer         │
              │                                 │
              │  Pretrained ECG Models         │
              │  Signal Extraction             │
              │  Layout Identification         │
              │  Waveform Reconstruction       │
              └──────────────┬──────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Generated Outputs    │
                  │                      │
                  │ CSV                  │
                  │ Digital ECG PNG      │
                  │ Metadata             │
                  └──────────────────────┘
Project Structure
ecg-digitization/
│
├── app/
│   ├── __init__.py
│   │
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── ecg.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── ecg.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ecg_service.py
│   │   ├── digitizer_service.py
│   │   ├── storage_service.py
│   │   └── file_validation_service.py
│   │
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── preprocessing.py
│   │   ├── image_classifier.py
│   │   ├── grid_removal.py
│   │   ├── waveform_extraction.py
│   │   └── reconstruction.py
│   │
│   └── models/
│       ├── __init__.py
│       └── ecg.py
│
├── models/
│   └── pretrained/
│
├── storage/
│   ├── originals/
│   ├── processed/
│   ├── signals/
│   └── metadata/
│
├── tests/
│   ├── __init__.py
│   ├── test_health.py
│   ├── test_ecg_upload.py
│   └── test_processing.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
Technology Stack
Backend
Python 3.11
FastAPI
Uvicorn
Pydantic
Pydantic Settings
Python Multipart
Image Processing
Pillow
ECG Digitization
Open-ECG-Digitizer
PyTorch
CUDA/GPU acceleration where available
Storage
Local filesystem
Installation
1. Clone the repository
git clone <repository-url>
cd ecg-digitization
2. Create virtual environment

Windows:

python -m venv .venv

Activate:

.venv\Scripts\activate

Linux/macOS:

python3 -m venv .venv
source .venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
Environment Configuration

Create a .env file using .env.example.

Example:

APP_NAME=ECG Digitization API
APP_VERSION=1.0.0
MAX_UPLOAD_SIZE_MB=10

The application also requires the Open-ECG-Digitizer environment and worker to be configured correctly.

Example configuration:

DIGITIZER_ROOT=<path-to-open-ecg-digitizer>
DIGITIZER_PYTHON=<path-to-digitizer-python>
DIGITIZER_WORKER=<path-to-worker.py>
Running the API

Start the FastAPI application:

uvicorn app.main:app --reload

The API will be available at:

http://127.0.0.1:8000

Swagger documentation:

http://127.0.0.1:8000/docs

ReDoc:

http://127.0.0.1:8000/redoc
API Documentation
Health Check
Request
GET /health
Response
{
  "status": "healthy",
  "service": "ECG Digitization API",
  "version": "1.0.0"
}
Upload ECG
Request
POST /api/v1/ecg

Content type:

multipart/form-data

Parameter:

file: ECG image

Supported formats:

JPEG
PNG
Example Response
{
  "ecg_id": "ecg_915ed43df1d347e48cc3e912b4ef07d6",
  "status": "digitized",
  "original_filename": "ecg.png",
  "layout": "Unknown layout",
  "matching_cost": 1.0,
  "extracted_leads": [
    "V1",
    "V2",
    "V3",
    "V4"
  ],
  "sample_count": 5000,
  "waveform": {
    "format": "csv",
    "available": true
  },
  "digital_ecg": {
    "format": "png",
    "available": true
  }
}
Get Processing Status
Request
GET /api/v1/ecg/{ecg_id}/status
Example Response
{
  "ecg_id": "ecg_915ed43df1d347e48cc3e912b4ef07d6",
  "status": "completed"
}

Possible processing states:

pending
processing
completed
failed
Get Waveform
Request
GET /api/v1/ecg/{ecg_id}/waveform

Returns the generated ECG waveform CSV.

The canonical output contains ECG lead columns such as:

I
II
III
aVR
aVL
aVF
V1
V2
V3
V4
V5
V6
Get Digital ECG
Request
GET /api/v1/ecg/{ecg_id}/digital

Returns the generated digital ECG image as PNG.

Processing Lifecycle

Each ECG follows a controlled processing lifecycle.

pending
   │
   ▼
processing
   │
   ├──────────────► completed
   │
   ▼
 failed
Pending

The ECG processing job has been created.

Processing

The image has been stored and the digitizer is processing it.

Completed

Required waveform output has been successfully generated.

Failed

Processing failed due to an error, timeout, worker failure, or missing required output.

Error Handling

The API performs multiple levels of validation and error handling.

Invalid file

Examples:

Unsupported extension
Invalid content type
Empty file
File larger than configured limit
Invalid image data

These requests are rejected before digitization.

Digitizer failure

If the digitizer fails:

processing
    ↓
failed

Partial processing files are removed.

The original uploaded ECG image is preserved.

Worker timeout

The digitizer worker has a processing timeout.

If the worker becomes unresponsive:

timeout
   ↓
worker force stopped
   ↓
processing failed
   ↓
partial files cleaned

This prevents a hung ML process from remaining alive indefinitely.

Worker Architecture

The Open-ECG-Digitizer is executed as a separate long-running worker process.

The FastAPI application communicates with the worker using JSON messages over stdin/stdout.

Example request:

{
  "command": "digitize",
  "image_path": "...",
  "output_dir": "...",
  "output_name": "ecg_123"
}

The worker returns a JSON response containing the processing result and generated output information.

This design keeps the API layer separate from the ML inference environment.

Storage Structure

For an ECG with ID:

ecg_123

the storage structure is:

storage/
│
├── originals/
│   └── ecg_123.png
│
├── signals/
│   └── ecg_123/
│       ├── ecg_123.png
│       └── ecg_123_timeseries_canonical.csv
│
└── metadata/
    └── ecg_123/
        ├── metadata.json
        └── status.json
Originals

Contains the original uploaded ECG image.

Signals

Contains generated waveform and digital ECG outputs.

Metadata

Contains processing metadata and current processing status.

Why a Separate Worker?

The digitizer uses heavy ML dependencies and may use GPU acceleration.

Instead of loading the ML environment directly into the FastAPI application, the backend starts a separate worker process.

Benefits:

Separation of API and ML runtime
Independent Python environments
Worker lifecycle management
Timeout handling
Crash detection
Graceful shutdown
Easier future scaling
Production-Oriented Reliability

The backend includes basic production-oriented reliability mechanisms:

Input Validation
       ↓
Unique Job ID
       ↓
Persistent Original
       ↓
Processing Status
       ↓
Worker Monitoring
       ↓
Output Verification
       ↓
Success / Failure

The system also avoids exposing internal exceptions directly to API clients.

Detailed errors are logged on the server while clients receive controlled error messages.

Testing

Run the test suite using:

pytest

Recommended validation scenarios:

1. Valid ECG

Expected:

200 OK
status = completed
CSV generated
PNG generated
2. Invalid file

Expected:

4xx
3. Digitizer failure

Expected:

status = failed
partial outputs removed
original preserved
4. Worker timeout

Expected:

worker stopped
processing marked failed
partial outputs cleaned
Important Scope

This project performs ECG image digitization.

The generated waveform should be treated as digitized/reconstructed signal data. The system does not by itself establish clinical accuracy, diagnostic validity, or equivalence to an original ECG acquisition device.

Any clinical use would require appropriate validation and domain-specific verification.

Future Improvements

Possible future extensions include:

Digital-vs-scanned ECG detection
Database-backed job metadata
Cloud/object storage
Background job queue
Redis/Celery or similar worker architecture
Authentication and authorization
Rate limiting
Metrics and monitoring
Distributed processing
GPU worker scaling
Automated model validation
More comprehensive automated tests
License

Add the appropriate license for this project and verify the licensing requirements of the integrated Open-ECG-Digitizer project before redistribution.


## GitHub repository description

GitHub ke **Description** field me ye daal:

> **Production-oriented FastAPI backend for ECG image digitization using the Open-ECG-Digitizer inference engine, generating machine-readable waveform CSV, digital ECG images, metadata, and processing status.**

### Short version

> **FastAPI backend for ECG image digitization and waveform extraction using Open-ECG-Digitizer.**

**Main short version recommend karunga** GitHub description ke liye; README me detailed version rakho.