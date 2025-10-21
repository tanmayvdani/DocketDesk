#include <iostream>
#if __has_include(<filesystem>)
    #include <filesystem>
    namespace fs = std::filesystem;
#elif __has_include(<experimental/filesystem>)
    #include <experimental/filesystem>
    namespace fs = std::experimental::filesystem;
#else
    #error "No filesystem support found."
#endif
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>
#include <cctype>
#include <unordered_map>
#include <sstream>
#include <cstdio> // For _popen, _pclose
#include <array>  // For std::array


struct Client {
    std::string first;
    std::string middle;
    std::string last;

    std::string baseFolderName() const {
        if (middle.empty()) return last + "_" + first;
        return last + "_" + middle + "_" + first;
    }
};

// ======================= Utility ============================
std::string toLower(const std::string &s) {
    std::string out(s);
    std::transform(out.begin(), out.end(), out.begin(), 
                   [](unsigned char c){ return std::tolower(c); });
    return out;
}

bool hasValidExtension(const fs::path &p) {
    std::string ext = toLower(p.extension().string());
    return ext == ".pdf" || ext == ".docx" || ext == ".txt";
}

std::string readTextFile(const fs::path &p) {
    std::ifstream in(p, std::ios::in | std::ios::binary);
    if (!in) return {};
    std::ostringstream ss;
    ss << in.rdbuf();
    return ss.str();
}

std::string extractText(const fs::path &p) {
    std::string ext = toLower(p.extension().string());

    if (ext == ".txt") {
        return readTextFile(p);
    } else if (ext == ".pdf" || ext == ".docx") {
        std::string command = "python read_files.py \"" + p.string() + "\"";
        std::array<char, 4096> buffer; // Increased buffer size
        std::string result;
        
        std::cerr << "DEBUG: Executing command: " << command << std::endl; // Debug print

        FILE* pipe = _popen(command.c_str(), "r");
        if (!pipe) {
            std::cerr << "Error: _popen failed for command: " << command << std::endl;
            return {};
        }
        while (fgets(buffer.data(), buffer.size(), pipe) != nullptr) {
            result += buffer.data();
        }
        int pclose_status = _pclose(pipe);
        std::cerr << "DEBUG: _pclose status: " << pclose_status << std::endl; // Debug print
        std::cerr << "DEBUG: Raw output from pipe: \n" << result << std::endl; // Debug print
        return result;
    }
    return {};
}

bool filenameHasNames(const fs::path &p, const std::string &first, 
                      const std::string &last) {
    std::string name = toLower(p.filename().string());
    return name.find(toLower(first)) != std::string::npos &&
           name.find(toLower(last)) != std::string::npos;
}

bool textHasNames(const std::string &text, const std::string &first, 
                  const std::string &last) {
    if (text.empty()) return false;
    std::string lf = toLower(first), ll = toLower(last), lt = toLower(text);
    return (lt.find(lf) != std::string::npos && lt.find(ll) != std::string::npos);
}

void processFile(const fs::path &file, const std::vector<Client> &clients,
                 const std::vector<std::string> &folderNames,
                 const fs::path &destPath, bool doMove, int &matched) {
    bool found = false;
    
    // Check filename first
    for (size_t i = 0; i < clients.size() && !found; ++i) {
        const auto &c = clients[i];
        if (filenameHasNames(file, c.first, c.last)) {
            fs::path target = destPath / folderNames[i];
            fs::create_directories(target);
            try {
                if (doMove) 
                    fs::rename(file, target / file.filename());
                else 
                    fs::copy_file(file, target / file.filename(), 
                                 fs::copy_options::overwrite_existing);
                std::cout << "[FILENAME] " << file.filename() 
                         << " → " << folderNames[i] << "\n";
                matched++;
            } catch (const std::exception &e) {
                std::cerr << "Error: " << e.what() << "\n";
            }
            found = true;
        }
    }

    // Check content if not found by filename
    if (!found) {
        std::string text = extractText(file);
        
        for (size_t i = 0; i < clients.size() && !found; ++i) {
            const auto &c = clients[i];
            
            if (textHasNames(text, c.first, c.last)) {
                fs::path target = destPath / folderNames[i];
                fs::create_directories(target);
                try {
                    if (doMove) 
                        fs::rename(file, target / file.filename());
                    else 
                        fs::copy_file(file, target / file.filename(), 
                                     fs::copy_options::overwrite_existing);
                    std::cout << "[CONTENT] " << file.filename() 
                             << " → " << folderNames[i] << "\n";
                    matched++;
                } catch (const std::exception &e) {
                    std::cerr << "Error: " << e.what() << "\n";
                }
                found = true;
            }
        }
    }

    if (!found)
        std::cout << "[NO MATCH] " << file.filename() << "\n";
}

std::vector<Client> getClientsFromUser() {
    std::vector<Client> clients;
    std::cout << "\nEnter client names (First Middle(optional) Last), "
              << "type 'done' when finished:\n";
    
    while (true) {
        std::string line;
        std::getline(std::cin, line);
        if (toLower(line) == "done") break;
        if (line.empty()) continue;

        std::istringstream iss(line);
        std::vector<std::string> parts;
        std::string token;
        while (iss >> token) parts.push_back(token);

        if (parts.size() == 2)
            clients.push_back({parts[0], "", parts[1]});
        else if (parts.size() == 3)
            clients.push_back({parts[0], parts[1], parts[2]});
        else
            std::cerr << "Invalid input format.\n";
    }
    return clients;
}

std::vector<std::string> generateFolderNames(const std::vector<Client> &clients) {
    std::unordered_map<std::string, int> dup;
    std::vector<std::string> folderNames;
    
    for (const auto &c : clients) {
        std::string base = c.baseFolderName();
        int id = dup[base]++;
        folderNames.push_back(id == 0 ? base : base + "_" + std::to_string(id + 1));
    }
    return folderNames;
}

void displayClientMapping(const std::vector<Client> &clients,
                         const std::vector<std::string> &folderNames) {
    std::cout << "\nClient → Folder mapping:\n";
    for (size_t i = 0; i < clients.size(); ++i) {
        std::cout << "  " << clients[i].first << " " 
                  << (clients[i].middle.empty() ? "" : clients[i].middle + " ") 
                  << clients[i].last << " → " << folderNames[i] << "\n";
    }
}

std::vector<fs::path> collectFiles(const fs::path &srcPath) {
    std::vector<fs::path> files;
    for (auto &entry : fs::recursive_directory_iterator(srcPath)) {
        if (entry.is_regular_file() && hasValidExtension(entry.path()))
            files.push_back(entry.path());
    }
    return files;
}

// ======================= Main ============================
int main(int argc, char** argv) {
    bool doMove = (argc > 1 && std::string(argv[1]) == "--move");

    std::cout << "=============================\n";
    std::cout << " Lawyer File Organizer\n";
    std::cout << "=============================\n\n";

    // Get source and destination paths
    std::string srcPathStr, destPathStr;
    std::cout << "Enter source folder path: ";
    std::getline(std::cin, srcPathStr);
    std::cout << "Enter destination folder path: ";
    std::getline(std::cin, destPathStr);

    fs::path srcPath(srcPathStr);
    fs::path destPath(destPathStr);

    if (!fs::exists(srcPath) || !fs::is_directory(srcPath)) {
        std::cerr << "Error: Invalid source directory.\n";
        return 1;
    }

    try {
        if (!fs::exists(destPath)) 
            fs::create_directories(destPath);
    } catch (...) {
        std::cerr << "Error: Cannot create destination directory.\n";
        return 1;
    }

    // Get client information
    std::vector<Client> clients = getClientsFromUser();
    if (clients.empty()) {
        std::cerr << "No clients provided.\n";
        return 1;
    }

    // Generate folder names and display mapping
    std::vector<std::string> folderNames = generateFolderNames(clients);
    displayClientMapping(clients, folderNames);

    // Collect files
    std::vector<fs::path> files = collectFiles(srcPath);
    std::cout << "\nScanning " << files.size() << " files...\n\n";

    // Process each file
    int matched = 0;
    for (auto &file : files) {
        processFile(file, clients, folderNames, destPath, doMove, matched);
    }

    std::cout << "\nMatched " << matched << " files.\n";
    std::cout << (doMove ? "Files were MOVED.\n" : "Files were COPIED.\n");
    std::cout << "Done.\n";

    return 0;
}