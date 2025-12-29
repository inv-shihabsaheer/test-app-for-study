pipeline {
  agent any

  environment {
    PROJECT_ID = "my-gcp-project"
    REGION     = "us-central1"
    AR_REPO    = "my-artifact-repo"
    IMAGE_NAME = "myapp"

    CLUSTER = "my-gke-cluster"
    ZONE    = "us-central1-a"

    HELM_REPO_URL = "https://github.com/my-org/myapp-helm-repo.git"
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
          GIT_SHA = sh(
            script: "git rev-parse --short HEAD",
            returnStdout: true
          ).trim()
          IMAGE_TAG = "${GIT_SHA}-${env.BUILD_NUMBER}"
          echo "Image tag: ${IMAGE_TAG}"
        }
      }
    }

    stage('Build & Push Image') {
      steps {
        script {
          IMAGE_URI = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME}:${IMAGE_TAG}"

          sh """
            gcloud auth activate-service-account --key-file=$GCP_SA_KEY
            gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

            docker build -t ${IMAGE_URI} .
            docker push ${IMAGE_URI}
          """
        }
      }
    }

    stage('Deploy using Helm Repo') {
      steps {
        sh """
          rm -rf helm-repo
          git clone ${HELM_REPO_URL} helm-repo

          gcloud container clusters get-credentials ${CLUSTER} \
            --zone ${ZONE} --project ${PROJECT_ID}

          helm upgrade --install myapp helm-repo/myapp \
            --set image.repository=${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME} \
            --set image.tag=${IMAGE_TAG}
        """
      }
    }
  }
}
