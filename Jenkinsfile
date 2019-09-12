pipeline {
    agent none
    options {
        skipStagesAfterUnstable()
    }
    stages {
        stage('Deliver') {
            agent {
                docker {
                    image "cdrx/pyinstaller-windows:python2"
                    args "-u root --privileged -v /jenkins_home/jobs/lipidxplorer/workspace:/src --entrypoint=\'\'"
                    reuseNode true
                }
            }
            steps {
                sh 'pyinstaller --distpath="LipidXplorer-1.2.8.${BUILD_NUMBER}" --upx-dir=/usr/local/share/ LipidXplorer.spec'
            }
            post {
                success {
                    archiveArtifacts '/jenkins_home/jobs/pipeline_example/workspace/LipidXplorer-1.2.8.${BUILD_NUMBER}.zip'
                }
            }
        }
    }
}