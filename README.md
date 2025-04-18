## CSU AISW 시험 모니터링  
------
### How to run?
1. dockerfile을 이용한 docker build
```
docker build -t ${IMAGE_NAME} \
  --build-arg GITHUB_USERNAME=${GITHUB_USERNAME} \
  --build-arg GITHUB_TOKEN=${GITHUB_TOKEN} \
  --build-arg REPO_NAME=${REPO_NAME} \
  .
```
```{IMAGE_NAME}```: docker image 이름      
```{GITHUB_USERNAME}```: github ID   
```{GITHUB_TOKEN}```: github session에서 발급받은 token   
```{REPO_NAME}```: github repo 주소(뒤에 .git 빼고)   



2. 컨테이너 생성
```
docker run -it \
  --name ${CONTAINER_NAME} \
  --shm-size 16G \
  --ipc host \
  -p ${HOST_PORT}:${GUEST_PORT} \
  -e CSV_FILE=${CSV_FILE} \
  -e DB_FILE=${DB_FILE} \
  -e PORT=${GUEST_PORT} \
  -v $(pwd)/${CSV_FILE}:/workspace/${REPO_NAME}/${CSV_FILE} \
  -v $(pwd)/${DB_FILE}:/workspace/${REPO_NAME}/${DB_FILE} \
  ${IMAGE_NAME}
```
```{CONTAINER_NAME}```: docker container 이름      
```{HOST_PORT}```: 호스팅 컴퓨터 port   
```{GUEST_PORT}```: docker 내부 port   
```{REPO_NAME}```: github repo 주소(뒤에 .git 빼고)   
```{CSV_FILE}```: 학생 정보가 포함된 csv 파일   
```{DB_FILE}```: 저장 DB 파일



3. csv 파일 포맷
```
student_id,password,subject_code
20250000,1234,39566-02-mid
20250000,5678,39566-02-mid
...
```


4. 한 번에 실행하기
```run.sh```: 내부 변수명 조절 필요   