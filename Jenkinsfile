pipeline {
  agent any

  environment {
    PROJECT_ID    = "curser-project"
    REGION        = "us-central1"
    AR_REPO       = "my-artifact-repo"
    IMAGE_NAME    = "myapp"
    CLUSTER       = "my-gke-cluster"
    HELM_REPO_URL = "https://github.com/inv-shihabsaheer/test-app-for-study-helm-chart.git"

    PATH = "${PATH}:${HOME}/bin"
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
        export PATH=\$HOME/bin:\$PATH
        export USE_GKE_GCLOUD_AUTH_PLUGIN=True

        ARCH=\$(uname -m)
        echo "Detected architecture: \$ARCH"

        if [ "\$ARCH" = "x86_64" ]; then
          ARCH_DL="amd64"
        elif [ "\$ARCH" = "aarch64" ] || [ "\$ARCH" = "arm64" ]; then
          ARCH_DL="arm64"
        else
          echo "Unsupported architecture: \$ARCH"
          exit 1
        fi

        echo "Installing kubectl..."
        curl -fsSL https://dl.k8s.io/release/\$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/\$ARCH_DL/kubectl -o kubectl
        chmod +x kubectl
        mv kubectl \$HOME/bin/

        echo "Installing gke-gcloud-auth-plugin (FORCED)..."
        curl -fsSL https://github.com/GoogleCloudPlatform/cloud-sdk-gke-gcloud-auth-plugin/releases/latest/download/gke-gcloud-auth-plugin-linux-\$ARCH_DL \
          -o gke-gcloud-auth-plugin
        chmod +x gke-gcloud-auth-plugin
        mv gke-gcloud-auth-plugin \$HOME/bin/

        echo "Installing Helm..."
        HELM_VERSION=v3.19.4
        curl -fsSL https://get.helm.sh/helm-\${HELM_VERSION}-linux-\$ARCH_DL.tar.gz -o helm.tgz
        tar -zxf helm.tgz
        chmod +x linux-\$ARCH_DL/helm
        mv linux-\$ARCH_DL/helm \$HOME/bin/helm
        rm -rf linux-\$ARCH_DL helm.tgz

        echo "Authenticating to GCP..."
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
