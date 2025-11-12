import jenkins.model.Jenkins
import hudson.security.csrf.DefaultCrumbIssuer

def jenkins = Jenkins.getInstance()
def crumbIssuer = jenkins.getCrumbIssuer()

if (crumbIssuer == null) {
    println "CSRF protection is disabled"
} else {
    jenkins.setCrumbIssuer(null)
    jenkins.save()
    println "CSRF protection disabled"
}
