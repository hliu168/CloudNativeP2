node {
  	properties([disableConcurrentBuilds()])

 
    timestamps {
			stage('Clean Workspace') {
					cleanWs()
					deleteDir()
        	}
			checkout scm
    }
}
