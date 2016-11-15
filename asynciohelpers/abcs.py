from abc import abstractmethod, abstractproperty, ABCMeta


class ServiceBaseABC(metaclass=ABCMeta):

   @abstractproperty
   def _host(self):
      "host or IP to connect to"

   @abstractproperty
   def _port(self):
      "port to connect to"

   @abstractproperty
   def _ssl(self):
      "whether or not to use SSL"

   @abstractmethod
   def start(self):
      "call to start the service"

   @abstractmethod
   def stop(self):
      "call to stop the service"

   @abstractmethod
   def _setup(self):
      "after start is called, do some setup here"

   @abstractmethod
   def _run(self):
      "actually run the service"

   @abstractmethod
   def _teardown(self):
      "perform cleanup here after stop is called"


class WAMPServiceABC(metaclass=ABCMeta):

   @abstractproperty
   def wmp_url():
      ""

   @abstractproperty
   def wmp_realm():
      ""

   # OPTIONAL, SO NOT PART OF ABC
   #@abstractproperty
   #def wmp_ssl():
   #   ""

   @abstractproperty
   def wmp_sessioncomponent():
      ""

   @abstractproperty
   def wmp_serializers():
      ""

   @abstractproperty
   def wmp_extra():
      ""

   @abstractproperty
   def _transport_factory():
      ""

   @abstractmethod
   def _component():
      ""
