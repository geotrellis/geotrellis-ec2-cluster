TROPOSPHERE_SRC := $(wildcard troposphere/*_template.py)
CLOUDFORMATION_SRC := $(patsubst troposphere/%_template.py,troposphere/%_template.json,$(TROPOSPHERE_SRC))

troposphere/%_template.json: troposphere/%_template.py
	@python $< > $@
	@aws cloudformation validate-template --template-body file://$@ > /dev/null
	@echo "Template written and validated to $@"

build: $(CLOUDFORMATION_SRC)

clean:
	@rm -f troposphere/*.json

vpc-stack: build
	./deployment-helper.sh create-vpc-stack

private-hosted-zones:
	./deployment-helper.sh create-private-hosted-zones

leader-stack: build
	./deployment-helper.sh create-leader-stack

follower-stack: build
	./deployment-helper.sh create-follower-stack

leader-ami:
	./deployment-helper.sh create-leader-ami

follower-ami:
	./deployment-helper.sh create-follower-ami

.PHONY: build clean vpc-stack leader-stack follower-stack leader-ami follower-ami
