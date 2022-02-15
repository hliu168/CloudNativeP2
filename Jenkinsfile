node {
  	properties([disableConcurrentBuilds()])

 
    timestamps {
			stage('Clean Workspace') {
					cleanWs()
					deleteDir()
        	}
			checkout scm
	    stage('Checkout Workspace') {
		    dir ('subproject') {
		    checkout([$class: 'GitSCM',
                              branches: [[name: "origin/master"]],
                              doGenerateSubmoduleConfigurations: false,
                              extensions: [[$class: 'DisableRemotePoll'], [$class: 'PathRestriction', excludedRegions: '', includedRegions: '__nonexistent__']],
                              userRemoteConfigs: [[url: 'https://github.com/hliu168/CloudDevOpsP4.git']],
                              changelog: false, 
                              poll: false
                    ])
		    }
	    }
    }
}
