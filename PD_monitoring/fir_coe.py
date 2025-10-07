# You can choose to move these imports to the top level if desired.
import numpy as np
from scipy.signal import firwin

def generate_fir_coeff_vector(f_low_mhz, f_high_mhz, file_path, numtaps=128):
    """
    Generate FIR filter coefficients and save them as a C-language vector in a text file.
    
    Parameters:
        f_low_mhz (float): Lower cutoff frequency in MHz.
        f_high_mhz (float): Upper cutoff frequency in MHz.
        file_path (str): The path to the output file.
        numtaps (int, optional): Number of filter taps (default is 128).
    
    For a valid bandpass design, the cutoff frequencies must satisfy:
        0 < f_low_mhz < f_high_mhz < (fs/2 in MHz)  (here fs/2 = 125 MHz for fs = 250 MHz).
    If the input parameters are invalid (e.g. out of range or f_low equals f_high),
    an all-pass filter is generated instead.
    
    The function uses a fixed sampling frequency of 250 MHz and a Hamming window.
    It converts the cutoff frequencies from MHz to Hz, designs a bandpass FIR filter using firwin,
    and writes the coefficients to the specified file in the following C vector format:
    
        float fir_coeff[] = {
            -0.0000378638,
            -0.0003378289,
            ...
            -0.0000378638
        };
    """
    # Fixed parameters
    fs = 250e6              # Sampling frequency in Hz (250 MHz)
    window_type = "hamming"  # Window type
    f_aaf = 140e6
    # Check if the cutoff frequencies are valid:
    # They must be in (0, fs/2) and f_low_mhz must be less than f_high_mhz.
    if (f_low_mhz <= 0) or (f_high_mhz >= (f_aaf/2) / 1e6) or (abs(f_low_mhz - f_high_mhz) < 1e-9):
        if f_low_mhz <= 0:
            print("进入if：因为 f_low_mhz <= 0")
        if f_high_mhz >= (f_aaf/2) / 1e6:
            print("进入if：因为 f_high_mhz >= (f_aaf/2)/1e6")
        if abs(f_low_mhz - f_high_mhz) < 1e-9:
            print("进入if：因为 f_low_mhz 与 f_high_mhz 基本相等")
        print("Invalid cutoff frequencies provided. Generating an all-pass filter.")
        coeff = np.zeros(numtaps)
        if (numtaps % 2 == 1):
            center = numtaps // 2
            coeff[center] = 1.0
        else:
            center = numtaps // 2
            coeff[center - 1] = 0.5
            coeff[center] = 0.5
    else:
        # Convert cutoff frequencies from MHz to Hz (inputs are float)
        f_low = f_low_mhz * 1e6
        f_high = f_high_mhz * 1e6

        # Normalize cutoff frequencies for firwin: 1 corresponds to fs/2.
        cutoff = [f_low / (fs / 2), f_high / (fs / 2)]
        print("Normalized cutoff frequencies:", cutoff)

        # Design the bandpass FIR filter (pass_zero=False indicates a bandpass filter)
        coeff = firwin(numtaps, cutoff, pass_zero=False, window=window_type)

    # Generate C-language vector format
    c_vector_lines = []
    # c_vector_lines.append("float fir_coeff[] = {")
    c_vector_lines.append(",\n".join(f"    {x:.10f}" for x in coeff))
    # c_vector_lines.append("};")
    c_vector_content = "\n".join(c_vector_lines)

    # Write the C vector to the specified file
    with open(file_path, "w") as f:
        f.write(c_vector_content)

    print(f"FIR coefficients vector file saved to {file_path}")


if __name__ == '__main__':

    
    # Specify output file path (adjust the path as needed)
    output_file = "fir_coefficients_vector.txt"
    
    # Generate the FIR coefficient vector file
    generate_fir_coeff_vector(5, 60.0, output_file)
