pipeline {
  agent any

  environment {
    PROJECT_ID    = "curser-project"
    REGION        = "us-central1"
    AR_REPO       = "my-artifact-repo"
    IMAGE_NAME    = "myapp"
    CLUSTER       = "my-gke-cluster"
    HELM_REPO_URL = "https://github.com/inv-shihabsaheer/test-app-for-study-helm-chart.git"

    PATH = "${env.PATH}:${env.HOME}/bin"
    USE_GKE_GCLOUD_AUTH_PLUGIN = "True"
  }

  stages {

    stage('Checkout App Repo') {
      steps {
        checkout scm
      }
    }

    stage('Generate Image Tag') {
      steps {
        script {
          def GIT_SHA = sh(
            script: 'git rev-parse --short HEAD',
            returnStdout: true
          ).trim()
          env.IMAGE_TAG = "${GIT_SHA}-${env.BUILD_NUMBER}"
          echo "Image tag: ${env.IMAGE_TAG}"
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

    stage('Deploy using Helm') {
      steps {
        withCredentials([
          file(credentialsId: 'GCP_SA_KEY', variable: 'GCP_KEY_FILE')
        ]) {
          sh """
            set -e

            mkdir -p \$HOME/bin

            echo "Installing kubectl..."
            if ! command -v kubectl >/dev/null 2>&1; then
              curl -LO https://dl.k8s.io/release/\$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl
              chmod +x kubectl
              mv kubectl \$HOME/bin/
            fi

            echo "Installing gke-gcloud-auth-plugin..."
            if ! command -v gke-gcloud-auth-plugin >/dev/null 2>&1; then
              curl -LO https://github.com/GoogleCloudPlatform/cloud-sdk-gke-gcloud-auth-plugin/releases/latest/download/gke-gcloud-auth-plugin-linux-amd64
              chmod +x gke-gcloud-auth-plugin-linux-amd64
              mv gke-gcloud-auth-plugin-linux-amd64 \$HOME/bin/gke-gcloud-auth-plugin
            fi

            echo "Installing Helm..."
            if ! command -v helm >/dev/null 2>&1; then
              HELM_VERSION=v3.19.4
              curl -LO https://get.helm.sh/helm-\${HELM_VERSION}-linux-amd64.tar.gz
              tar -zxvf helm-\${HELM_VERSION}-linux-amd64.tar.gz
              chmod +x linux-amd64/helm
              mv linux-amd64/helm \$HOME/bin/helm
              rm -rf linux-amd64 helm-\${HELM_VERSION}-linux-amd64.tar.gz
            fi

            gcloud auth activate-service-account --key-file="\$GCP_KEY_FILE"
            gcloud config set project ${PROJECT_ID}

            rm -rf helm-repo
            git clone ${HELM_REPO_URL} helm-repo

            gcloud container clusters get-credentials ${CLUSTER} \
              --region ${REGION} \
              --project ${PROJECT_ID}

            helm upgrade --install myapp helm-repo/myapp \
              --set image.repository=${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME} \
              --set image.tag=${IMAGE_TAG}
          """
        }
      }
    }
  }

  post {
    success {
      echo "✅ Pipeline completed successfully"
    }
    failure {
      echo "❌ Pipeline failed"
    }
    always {
      cleanWs()
    }
  }
}
