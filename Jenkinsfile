pipeline {
  agent any

  /***********************
   * PARAMETERS (USER SELECTS)
   ***********************/
  parameters {
    booleanParam(
      name: 'CREATE_CLUSTER',
      defaultValue: false,
      description: 'Create GKE Autopilot cluster if it does not exist'
    )
  }

  /***********************
   * ENVIRONMENT
   ***********************/
  environment {
    PROJECT_ID    = "curser-project"
    REGION        = "us-central1"
    AR_REPO       = "my-artifact-repo"
    IMAGE_NAME    = "myapp"
    CLUSTER       = "my-gke-cluster"

    HELM_REPO_URL = "https://github.com/inv-shihabsaheer/test-app-for-study-helm-chart.git"
    HELM_REPO_DIR = "helm-repo"
    HELM_CHART    = "myapp"
  }

  stages {

    stage('Checkout App Repo') {
      steps {
        checkout scm
      }
    }

    /***********************
     * AUTOPILOT CLUSTER (OPTIONAL)
     ***********************/
    stage('Create GKE Autopilot Cluster (Optional)') {
      when {
        expression {
          return params.CREATE_CLUSTER == true
        }
      }
      steps {
        withCredentials([
          file(credentialsId: 'GCP_SA_KEY', variable: 'GCP_KEY_FILE')
        ]) {
          sh """
            set -e

            gcloud auth activate-service-account --key-file="\$GCP_KEY_FILE"
            gcloud config set project ${PROJECT_ID}

            echo "CREATE_CLUSTER=${params.CREATE_CLUSTER}"

            if gcloud container clusters describe ${CLUSTER} \
              --region ${REGION} \
              --project ${PROJECT_ID} >/dev/null 2>&1; then
              echo "✅ GKE cluster already exists"
            else
              echo "🚀 Creating GKE Autopilot cluster..."

              gcloud container clusters create-auto ${CLUSTER} \
                --region ${REGION} \
                --project ${PROJECT_ID}

              echo "✅ GKE Autopilot cluster created"
            fi
          """
        }
      }
    }

    stage('Generate Image Tag') {
      steps {
        script {
          def sha = sh(
            script: 'git rev-parse --short HEAD',
            returnStdout: true
          ).trim()
          env.IMAGE_TAG = "${sha}-${env.BUILD_NUMBER}"
        }
      }
    }

    stage('Build & Push Image') {
      steps {
        script {
          env.IMAGE_URI =
            "${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME}:${env.IMAGE_TAG}"

          withCredentials([
            file(credentialsId: 'GCP_SA_KEY', variable: 'GCP_KEY_FILE')
          ]) {
            sh """
              set -e
              gcloud auth activate-service-account --key-file="\$GCP_KEY_FILE"
              gcloud config set project ${PROJECT_ID}
              gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet
              docker build -t ${IMAGE_URI} .
              docker push ${IMAGE_URI}
            """
          }
        }
      }
    }

    stage('Update Helm Repo Image Tag (GitOps)') {
      steps {
        withCredentials([
          string(credentialsId: 'GITHUB_TOKEN', variable: 'GITHUB_TOKEN')
        ]) {
          sh """
            set -e
            rm -rf ${HELM_REPO_DIR}
            git clone https://x-access-token:\$GITHUB_TOKEN@github.com/inv-shihabsaheer/test-app-for-study-helm-chart.git ${HELM_REPO_DIR}
            cd ${HELM_REPO_DIR}/${HELM_CHART}

            sed -i 's|^  repository:.*|  repository: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME}|' values.yaml
            sed -i 's|^  tag:.*|  tag: ${IMAGE_TAG}|' values.yaml

            git config user.name "Jenkins CI"
            git config user.email "jenkins@ci.local"

            git add values.yaml
            git commit -m "ci: update image tag to ${IMAGE_TAG}" || true
            git push origin main
          """
        }
      }
    }

    stage('Deploy using Helm') {
      steps {
        withCredentials([
          file(credentialsId: 'GCP_SA_KEY', variable: 'GCP_KEY_FILE')
        ]) {
          sh """
            set -e
            gcloud auth activate-service-account --key-file="\$GCP_KEY_FILE"
            gcloud config set project ${PROJECT_ID}
            gcloud container clusters get-credentials ${CLUSTER} \
              --region ${REGION} \
              --project ${PROJECT_ID}

            helm upgrade --install myapp ${HELM_REPO_DIR}/${HELM_CHART} \
              --set image.repository=${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME} \
              --set image.tag=${IMAGE_TAG}
          """
        }
      }
    }
  }

  post {
    success { echo "✅ Pipeline completed successfully" }
    failure { echo "❌ Pipeline failed" }
    always  { cleanWs() }
  }
}
