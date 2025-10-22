To do:

  I. Modify `Fileorganizer.cpp` (C++ Backend):

   1. Command-Line Arguments:
       * Refactor main to accept source path, destination path, doMove flag, and client names as command-line arguments

   2. Structured Output:
       * Implement structured output (e.g., JSON or delimited strings) to stdout for communication with the GUI. This includes messages for file processing status, errors, and progress
        updates.

   3. Error Handling & Exit Codes:
       * Utilize distinct exit codes for various success/failure conditions, which the Python GUI can then interpret.

  II. Modify `PythonLawUI.py` (Python GUI Frontend):

   1. Asynchronous C++ Execution:
       * On "Start Processing" button click, use Python's subprocess.Popen to launch Fileorganizer.exe.
       * Execute this subprocess asynchronously (e.g., in a separate thread or using asyncio) to maintain GUI responsiveness.
       * Dynamically build the command-line argument list for Fileorganizer.exe from the GUI's input fields (source/destination paths, doMove checkbox, client list).
       * Redirect stdout and stderr of the C++ subprocess to pipes.
       * Asynchronously read and parse the structured output from these pipes.
       * Update the ActivityLog Component and ProcessingPanel Component (progress bar, status text) based on the parsed messages.

   2. Processing Controls (Pause/Stop):
       * Pause: Requires implementing a signal-handling mechanism in the C++ application (e.g., checking a flag file or listening for a signal) that the Python GUI can trigger.
       * Stop: The Python GUI can terminate the C++ subprocess using process.terminate(). The C++ application should ideally handle this termination gracefully.

   3. Error Handling:
       * Monitor the C++ subprocess's exit code and log any non-zero codes as errors in the ActivityLog.
       * Implement error handling for subprocess creation and communication.

