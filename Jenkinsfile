pipeline {
  agent any

  environment {
    PROJECT_ID = "curser-project"
    REGION     = "us-central1"
    AR_REPO    = "my-artifact-repo"
    IMAGE_NAME = "myapp"
    CLUSTER    = "my-gke-cluster"
    HELM_REPO_URL = "https://github.com/inv-shihabsaheer/test-app-for-study-helm-chart.git"
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
            sh '''
              set -e

              echo "Authenticating to GCP..."
              gcloud auth activate-service-account --key-file="$GCP_KEY_FILE"
              gcloud config set project "$PROJECT_ID"

              echo "Configuring Docker for Artifact Registry..."
              gcloud auth configure-docker $REGION-docker.pkg.dev --quiet

              echo "Building Docker image..."
              docker build -t $IMAGE_URI .

              echo "Pushing Docker image..."
              docker push $IMAGE_URI
            '''
          }
        }
      }
    }

    stage('Deploy using Helm') {
      steps {
        withCredentials([
          file(credentialsId: 'GCP_SA_KEY', variable: 'GCP_KEY_FILE')
        ]) {
          sh '''
            set -e

            echo "Authenticating to GCP..."
            gcloud auth activate-service-account --key-file="$GCP_KEY_FILE"
            gcloud config set project "$PROJECT_ID"

            echo "Installing kubectl if missing..."
            if ! command -v kubectl >/dev/null 2>&1; then
              gcloud components install kubectl --quiet
            fi

            echo "Installing GKE auth plugin if missing..."
            if ! command -v gke-gcloud-auth-plugin >/dev/null 2>&1; then
              gcloud components install gke-gcloud-auth-plugin --quiet
            fi

            echo "Installing Helm if missing..."
            if ! command -v helm >/dev/null 2>&1; then
              curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
            fi

            echo "Cloning Helm repo..."
            rm -rf helm-repo
            git clone "$HELM_REPO_URL" helm-repo

            echo "Getting GKE credentials..."
            gcloud container clusters get-credentials "$CLUSTER" \
              --region "$REGION" \
              --project "$PROJECT_ID"

            echo "Deploying application with Helm..."
            helm upgrade --install myapp helm-repo/myapp \
              --set image.repository=$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/$IMAGE_NAME \
              --set image.tag=$IMAGE_TAG
          '''
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
