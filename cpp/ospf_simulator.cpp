// ============================================================
//  ospf_simulator.cpp - Shortest Path First (Dijkstra) simulator
//
//  OSPF routers each build a map of the network (the link-state
//  database) and run Dijkstra's algorithm to find the cheapest path
//  to every other router. This program does the same:
//    1. Reads a topology file (router pairs + link cost)
//    2. Prints the routing table of a chosen router
//       (destination, next hop, total cost, full path)
//    3. Lets you fail a link and watch the routes re-converge
//
//  Build:  g++ -std=c++17 -Wall -O2 ospf_simulator.cpp -o ospf_simulator
//  Run:    ./ospf_simulator topology.txt
// ============================================================

#include <algorithm>
#include <climits>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <queue>
#include <sstream>
#include <string>
#include <vector>

using namespace std;

class Network {
public:
    // Load "A B COST" lines; '#' starts a comment. Returns false on error.
    bool load(const string& filename) {
        ifstream file(filename);
        if (!file) {
            cerr << "Cannot open " << filename << "\n";
            return false;
        }
        string line;
        int lineNo = 0;
        while (getline(file, line)) {
            ++lineNo;
            line = line.substr(0, line.find('#'));
            istringstream in(line);
            string a, b;
            int cost;
            if (!(in >> a)) continue;  // blank or comment line
            if (!(in >> b >> cost) || cost <= 0) {
                cerr << "Bad line " << lineNo << ": " << line << "\n";
                return false;
            }
            addLink(a, b, cost);
        }
        return true;
    }

    void addLink(const string& a, const string& b, int cost) {
        links[a][b] = cost;  // links are bidirectional
        links[b][a] = cost;
    }

    bool removeLink(const string& a, const string& b) {
        if (!links.count(a) || !links[a].count(b)) return false;
        links[a].erase(b);
        links[b].erase(a);
        return true;
    }

    bool hasRouter(const string& r) const { return links.count(r) > 0; }

    void printLinks() const {
        cout << "\nLink-state database (each link listed once):\n";
        for (const auto& [router, neighbours] : links)
            for (const auto& [nb, cost] : neighbours)
                if (router < nb)
                    cout << "  " << left << setw(12) << router << "<-->  "
                         << setw(12) << nb << "cost " << cost << "\n";
    }

    // Dijkstra's algorithm from `source`, then print an OSPF-style routing table.
    void printRoutingTable(const string& source) const {
        map<string, int> dist;
        map<string, string> prev;
        for (const auto& entry : links) dist[entry.first] = INT_MAX;
        dist[source] = 0;

        // min-heap of (distance, router)
        using Item = pair<int, string>;
        priority_queue<Item, vector<Item>, greater<Item>> pq;
        pq.push({0, source});

        while (!pq.empty()) {
            auto [d, u] = pq.top();
            pq.pop();
            if (d > dist[u]) continue;  // stale entry
            for (const auto& [v, cost] : links.at(u)) {
                if (dist[u] + cost < dist[v]) {
                    dist[v] = dist[u] + cost;
                    prev[v] = u;
                    pq.push({dist[v], v});
                }
            }
        }

        cout << "\nRouting table of " << source << "\n";
        cout << "  " << left << setw(14) << "Destination" << setw(14) << "Next hop"
             << setw(7) << "Cost" << "Path\n";
        cout << "  " << string(60, '-') << "\n";

        for (const auto& [dest, d] : dist) {
            if (dest == source) continue;
            if (d == INT_MAX) {
                cout << "  " << left << setw(14) << dest << setw(14) << "-"
                     << setw(7) << "inf" << "UNREACHABLE\n";
                continue;
            }
            // walk back from destination to source to rebuild the path
            vector<string> path;
            for (string at = dest; at != source; at = prev.at(at)) path.push_back(at);
            path.push_back(source);
            reverse(path.begin(), path.end());

            string pathStr;
            for (size_t i = 0; i < path.size(); ++i)
                pathStr += (i ? " -> " : "") + path[i];

            cout << "  " << left << setw(14) << dest << setw(14) << path[1]
                 << setw(7) << d << pathStr << "\n";
        }
    }

private:
    map<string, map<string, int>> links;  // router -> (neighbour -> cost)
};

static void showMenu() {
    cout << "\nCommands:\n"
            "  table <router>      show routing table\n"
            "  fail <A> <B>        bring a link down\n"
            "  add <A> <B> <cost>  add / restore a link\n"
            "  links               show all links\n"
            "  quit\n";
}

int main(int argc, char* argv[]) {
    string file = argc > 1 ? argv[1] : "topology.txt";
    Network net;
    if (!net.load(file)) return 1;

    cout << "=== OSPF Shortest Path First Simulator ===\n";
    net.printLinks();
    net.printRoutingTable("R1-HQ");
    showMenu();

    string line;
    while (cout << "\nospf> " && getline(cin, line)) {
        istringstream in(line);
        string cmd, a, b;
        in >> cmd;
        if (cmd == "quit" || cmd == "exit") break;
        if (cmd == "links") {
            net.printLinks();
        } else if (cmd == "table" && in >> a) {
            if (net.hasRouter(a)) net.printRoutingTable(a);
            else cout << "Unknown router " << a << "\n";
        } else if (cmd == "fail" && in >> a >> b) {
            if (net.removeLink(a, b))
                cout << "%OSPF-5-ADJCHG: link " << a << " <-> " << b
                     << " is DOWN. Recalculating SPF...\n";
            else
                cout << "No such link\n";
        } else if (cmd == "add") {
            int cost;
            if (in >> a >> b >> cost && cost > 0) {
                net.addLink(a, b, cost);
                cout << "Link " << a << " <-> " << b << " is UP (cost " << cost << ")\n";
            } else {
                cout << "Usage: add <A> <B> <cost>\n";
            }
        } else if (!cmd.empty()) {
            showMenu();
        }
    }
    return 0;
}
