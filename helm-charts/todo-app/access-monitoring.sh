#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📊 Todo App Monitoring Access${NC}"
echo "=============================="
echo ""
echo "Select a monitoring tool to access:"
echo ""
echo "1) Grafana (Dashboards)"
echo "2) Prometheus (Metrics)"
echo "3) Jaeger (Tracing)"
echo "4) AlertManager (Alerts)"
echo "5) All (Open all in background)"
echo "6) Stop all port-forwards"
echo "7) Show monitoring pods status"
echo "0) Exit"
echo ""
read -p "Enter choice [0-7]: " choice

case $choice in
    1)
        echo -e "${GREEN}Opening Grafana...${NC}"
        echo "URL: http://localhost:3000"
        echo "Username: admin"
        echo "Password: admin"
        kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80
        ;;
    2)
        echo -e "${GREEN}Opening Prometheus...${NC}"
        echo "URL: http://localhost:9090"
        kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090
        ;;
    3)
        echo -e "${GREEN}Opening Jaeger...${NC}"
        echo "URL: http://localhost:16686"
        kubectl port-forward -n monitoring svc/jaeger-query 16686:16686
        ;;
    4)
        echo -e "${GREEN}Opening AlertManager...${NC}"
        echo "URL: http://localhost:9093"
        kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-alertmanager 9093:9093
        ;;
    5)
        echo -e "${GREEN}Starting all monitoring tools...${NC}"

        # Kill any existing port-forwards
        pkill -f "port-forward.*monitoring" 2>/dev/null || true

        # Start port-forwards in background
        kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80 > /dev/null 2>&1 &
        kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090 > /dev/null 2>&1 &
        kubectl port-forward -n monitoring svc/jaeger-query 16686:16686 > /dev/null 2>&1 &
        kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-alertmanager 9093:9093 > /dev/null 2>&1 &

        sleep 3

        echo ""
        echo -e "${GREEN}✅ All monitoring tools are now accessible:${NC}"
        echo ""
        echo "  Grafana:      http://localhost:3000 (admin/admin)"
        echo "  Prometheus:   http://localhost:9090"
        echo "  Jaeger:       http://localhost:16686"
        echo "  AlertManager: http://localhost:9093"
        echo ""
        echo -e "${YELLOW}Press Enter to stop all port-forwards...${NC}"
        read
        pkill -f "port-forward.*monitoring"
        echo "All port-forwards stopped."
        ;;
    6)
        echo -e "${YELLOW}Stopping all port-forwards...${NC}"
        pkill -f "port-forward.*monitoring" 2>/dev/null || true
        echo -e "${GREEN}✅ All port-forwards stopped${NC}"
        ;;
    7)
        echo -e "${YELLOW}Monitoring pods status:${NC}"
        echo ""
        kubectl get pods -n monitoring
        echo ""
        echo -e "${YELLOW}Monitoring services:${NC}"
        echo ""
        kubectl get svc -n monitoring
        ;;
    0)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting..."
        exit 1
        ;;
esac
