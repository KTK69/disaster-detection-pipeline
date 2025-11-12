import jenkins.model.Jenkins
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition
import hudson.plugins.git.GitSCM
import hudson.plugins.git.UserRemoteConfig
import hudson.plugins.git.BranchSpec

def jenkins = Jenkins.getInstance()
def jobName = "disaster-detection-pipeline"

if (jenkins.getItem(jobName) == null) {
    def job = jenkins.createProject(WorkflowJob.class, jobName)
    job.setDescription("Disaster Detection MLOps Pipeline - Flood Detection for Visakhapatnam")
    
    def scm = new GitSCM("file:///workspace")
    scm.setBranches([new BranchSpec("*/main")])
    
    def flowDef = new CpsScmFlowDefinition(scm, "Jenkinsfile")
    flowDef.setLightweight(true)
    
    job.setDefinition(flowDef)
    jenkins.save()
    println "Job created successfully!"
} else {
    println "Job already exists"
}
