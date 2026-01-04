config_map_template = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: null
  namespace: null
  labels:
    app: null
data: null
"""

secret_template = """
apiVersion: v1
kind: Secret
metadata:
  name: null
  namespace: null
  labels:
    app: null
stringData: null
"""

deployment_template = """
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: null
  namespace: null
spec:
  replicas: null
  selector:
    matchLabels:
      app: null
  template:
    metadata:
      labels:
        app: null
    spec:
      containers: null
      restartPolicy: null
      volumes: null
"""

node_port_service_template = """
apiVersion: v1
kind: Service
metadata:
  name: null
  namespace: null
spec:
  type: NodePort
  selector:
    app: null
  ports:
    - port: null
      targetPort: null
      name: null
"""

pvc_template = """
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: null
  namespace: null
  labels:
    app: null
spec:
  storageClassName: null
  accessModes: null
  resources:
    requests:
      storage: null
"""
