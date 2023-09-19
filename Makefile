
###
### makefile: build the container 
### author:   ruggero.citton@oracle.com 
###


###########################
CONTAINER=ipcc
IMGNME=ip-change_check
IMGVRS=1
DOCKER=/usr/bin/docker
PODMAN=/usr/bin/podman
RUNTIMECT=$(DOCKER)


###############################################################################
#                             DOCKER/PODMAN SECTION                           #
###############################################################################

all: build \
	create \
	start \
	setup	

build:
	@echo "Make CONTAINER $(CONTAINER)"
	$(RUNTIMECT) build --force-rm=true \
	--no-cache=true -t $(IMGNME):$(IMGVRS) -f Dockerfile .

create:
	@echo "Create CONTAINER $(CONTAINER)"
    ifeq ($(RUNTIMECT),/usr/bin/docker)
		$(RUNTIMECT) create -t -i \
			--hostname $(CONTAINER) \
			--volume /etc/localtime:/etc/localtime:ro \
			--restart=always \
			--name $(CONTAINER) \
			$(IMGNME):$(IMGVRS)
    else
		$(RUNTIMECT) create -t -i \
			--hostname $(CONTAINER) \
			--volume /etc/localtime:/etc/localtime:ro \
			--restart=always \
			--name $(CONTAINER) \
			$(IMGNME):$(IMGVRS)
    endif

start:
	@echo "STARTING UP CONTAINER $(CONTAINER)"
	$(RUNTIMECT) start $(CONTAINER)

stop:
	@echo "STOPPING CONTAINER $(CONTAINER)"
	$(RUNTIMECT) stop $(CONTAINER)

clean:
	@echo "Cleanup CONTAINER $(CONTAINER)"
	-$(RUNTIMECT) stop $(CONTAINER)
	-$(RUNTIMECT) rm $(CONTAINER)
	$(RUNTIMECT) rmi $(IMGNME):$(IMGVRS)

connect:
	$(RUNTIMECT) exec -it $(CONTAINER) bash

test:
	$(RUNTIMECT) exec -it $(CONTAINER) python3 /app/notification_test.py

setup:
	$(RUNTIMECT) exec -it $(CONTAINER) python3 /app/initial_config.py
###############################################################################
#                                                                             #
###############################################################################
