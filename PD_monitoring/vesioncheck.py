def check_module_version(module_name, version_attribute="__version__"):
    try:
        module = __import__(module_name)
        version = getattr(module, version_attribute, "Version information not available")
        print(f"{module_name} version: {version}")
    except ImportError:
        print(f"{module_name} is not installed")

# OpenCV
check_module_version("cv2")

# Scikit-learn
check_module_version("sklearn")

# NumPy
check_module_version("numpy")

# Matplotlib
check_module_version("matplotlib")

# PyTorch and related libraries
check_module_version("torch")
check_module_version("torchvision")
check_module_version("torchaudio")

# tqdm
check_module_version("tqdm")

# kneed
check_module_version("kneed")

# Cython
check_module_version("Cython")
