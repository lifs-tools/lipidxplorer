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
                    args "-v ${PWD}:/src --entrypoint=\'\'"
                    reuseNode true
                }
            }
            steps {
                sh 'pyinstaller --distpath="/src/LipidXplorer-1.2.8.${BUILD_NUMBER}" /src/LipidXplorer.spec'
            }
            post {
                success {
                    archiveArtifacts '/src/LipidXplorer-1.2.8.${BUILD_NUMBER}.zip'
                }
            }
        }
    }
}