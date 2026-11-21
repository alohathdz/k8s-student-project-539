# Lab 539 การให้บริการหลายแอปด้วย Kubernetes

Nginx บน `k8s-lb` (192.168.29.20) ส่งคำขอไปยัง Traefik ผ่าน NodePort 30082 ของ Worker ที่ลงท้ายด้วย `.11` และ `.12` จากนั้น Traefik ส่งคำขอต่อไปยังแอป Flask ทั้งสามใน namespace `student-web` ส่วนบริการเดิม `nginx-lab` ใช้ NodePort 30081 และ `cluster-check` ใช้ NodePort 30080

| URL | บริการ | ผลที่คาดหวัง |
| --- | --- | --- |
| http://www.id-539.com/about | app-about | แสดงชื่อ รหัสนักศึกษา และรูปเมื่อกำหนดไว้ |
| http://www.id-539.com/research | app-research | แสดงสรุปงานวิจัยที่บันทึกไว้ |
| http://www.id-539.com/api/HelloK8s | app-api | แสดงข้อความ `HelloK8s` ขนาดใหญ่กลางหน้า |
| http://admin.id-539.com/edit | app-research | แสดงแบบฟอร์มแก้ไขหลังยืนยันตัวตนด้วย Basic Auth |
| http://admin.id-539.com/ | app-research | เปลี่ยนเส้นทางไปยัง `/edit` |

## ขั้นตอนติดตั้งและทดสอบ

เตรียมคลัสเตอร์ Kubernetes ที่ใช้พื้นที่จัดเก็บของ Lab หรือการตั้งค่าที่เทียบเท่า ตั้งค่า `kubectl` ให้เชื่อมต่อคลัสเตอร์ เตรียม Helm และ Docker ที่มีสิทธิ์ push อิมเมจ รวมถึง Nginx บนเครื่อง Load Balancer

1. Build และ push อิมเมจ `alohathdz/app-about:v1`, `alohathdz/app-api:v1` และ `alohathdz/app-research:v2` จากโฟลเดอร์ของแต่ละแอปใน `apps/` หากต้องยืนยันตัวตนเพื่อดึงอิมเมจ ให้กำหนด `imagePullSecrets` ใน Deployment หรือนำอิมเมจตรงรุ่นเข้า namespace `k8s.io` ของ containerd บน Worker แต่ละเครื่อง หากต้องใช้รูปนักศึกษา ให้เตรียมไฟล์รูปแยกไว้
2. ใช้ `kubectl apply` กับ `k8s/namespace.yaml` แล้วสร้าง Secret ชื่อ `research-admin` ใน `student-web` โดยกำหนดค่า `ADMIN_USER` และ `ADMIN_PASSWORD` ผ่านไฟล์ส่วนตัว ทั้งสองค่าต้องมีข้อมูล
3. ใช้ `kubectl apply` กับ `k8s/research-pv.yaml`, `k8s/research-pvc.yaml` และ manifest ของแอปทั้งสาม ตั้งค่า `STUDENT_NAME` และ `STUDENT_ID` ให้ Deployment `app-about` ตรวจสถานะ rollout และตรวจว่า PVC `research-data` อยู่ในสถานะ `Bound` หลังจัดวาง Pod
4. ติดตั้ง Traefik chart รุ่น `42.4.1` ใน namespace `traefik` ด้วย `--skip-crds` และไฟล์ `k8s/traefik-values.yaml` จากนั้นใช้ `kubectl apply` กับ `k8s/ingress.yaml` ทดสอบการส่งคำขอไปยัง Worker ทั้งสองโดยกำหนด `Host` header ให้ตรงกับโดเมนที่ทดสอบ
5. เพิ่มและเปิดใช้งาน `nginx/student-web.conf` เป็นไซต์แยกบนเครื่อง Load Balancer ตรวจไฟล์ตั้งค่าด้วย `nginx -t` ก่อน reload แล้วกำหนดให้ชื่อโดเมนทั้งสองชี้ไปที่ `192.168.29.20` ในไฟล์ hosts ของเครื่องทดสอบ
6. เปิดทั้งสี่หน้าบริการ บันทึกสรุปงานวิจัยผ่าน `/edit` แล้วสั่ง restart เฉพาะ `deployment/app-research` เปรียบเทียบเนื้อหาก่อนและหลัง restart จากนั้นตรวจอีกครั้งว่าบริการเดิมบน NodePort 30081 ยังตอบสนอง

พื้นที่จัดเก็บแบบคงที่ผูกกับ `k8s-worker1` และเก็บไว้เมื่อลบ PVC การทดสอบการกู้คืนครอบคลุมการเปลี่ยน Pod บน Worker เครื่องนี้

### คำสั่ง Kubernetes

รันคำสั่งจากโฟลเดอร์หลักของ repository และใช้ Kubernetes context ของ Lab สร้างไฟล์ตัวแปรสภาพแวดล้อมสิทธิ์ `0600` ไว้นอก repository ใส่ค่า `ADMIN_USER` และ `ADMIN_PASSWORD` แล้วแทนที่ `/secure/research-admin.env` ด้วยตำแหน่งไฟล์จริง หาก Worker ต้องยืนยันตัวตนเพื่อดึงอิมเมจ ให้ตั้งค่าสิทธิ์ก่อนติดตั้งแอป

```bash
kubectl apply -f k8s/namespace.yaml
kubectl -n student-web create secret generic research-admin \
  --from-env-file=/secure/research-admin.env
kubectl apply -f k8s/research-pv.yaml -f k8s/research-pvc.yaml
kubectl apply -f k8s/about.yaml -f k8s/api.yaml -f k8s/research.yaml
helm repo add traefik https://traefik.github.io/charts
helm repo update
helm upgrade --install traefik traefik/traefik --version 42.4.1 \
  --namespace traefik --create-namespace --skip-crds --wait \
  -f k8s/traefik-values.yaml
kubectl apply -f k8s/ingress.yaml
kubectl -n student-web get deployments,pods,services,ingress,pvc
kubectl -n student-web describe ingress student-ingress
kubectl -n student-web describe pvc research-data
```

เพิ่มสองบรรทัดจาก [config/linux-hosts.example](config/linux-hosts.example) ลงใน `/etc/hosts` ของเครื่อง Linux ที่ใช้ทดสอบ โดยเก็บรายการเดิมไว้ ตรวจการแปลงชื่อโดเมนเป็น IP ด้วย `getent hosts www.id-539.com admin.id-539.com`

Lab ใช้ HTTP ภายในเครือข่ายส่วนตัวของ VMware ให้เก็บภาพหน้าจอที่มีข้อมูลนักศึกษาไว้ในเอกสารหลักฐานสำหรับส่งงาน
