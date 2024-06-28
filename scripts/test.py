import os
import torch

# Print the path of the loaded torch module
print("PyTorch module path:", os.path.dirname(torch.__file__))

# Check if CUDA is available
cuda_available = torch.cuda.is_available()
print("CUDA available:", cuda_available)

# Print the CUDA version
cuda_version = torch.version.cuda
print("CUDA version:", cuda_version)

# Print the PyTorch version
torch_version = torch.__version__
print("PyTorch version:", torch_version)


if not torch.cuda.is_available():
    raise EnvironmentError("CUDA is not available. Please ensure that PyTorch is installed with CUDA support.")