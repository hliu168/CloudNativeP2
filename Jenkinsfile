node {
  	properties([disableConcurrentBuilds()])

  try {
    timestamps {
			stage('Clean Workspace') {
					cleanWs()
					deleteDir()
        	}
			checkout scm
    }
  }
}
