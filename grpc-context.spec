Name:		grpc-context
Version:	1.27.2
Release:	1
Summary:	gRPC context propagation
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/grpc/grpc-java
Source0:	https://github.com/grpc/grpc-java/archive/refs/tags/v%{version}.tar.gz#/grpc-context-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar

%description
grpc-context %{version} carries scoped values across API boundaries and
between threads. OpenCensus stores the current span in this context.

%prep
%autosetup -n grpc-java-%{version} -p1
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
find context/src/main/java -name '*.java' > sources.list
test "$(wc -l < sources.list)" -eq 4
mkdir -p classes
javac --release 8 -encoding UTF-8 \
	-d classes @sources.list
jar cf grpc-context.jar -C classes .
jar tf grpc-context.jar | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
javap -verbose -cp grpc-context.jar io.grpc.Context | grep -F 'major version: 52'

cat > grpc-context.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>io.grpc</groupId>
  <artifactId>grpc-context</artifactId>
  <version>1.27.2</version>
  <name>gRPC context propagation</name>
  <description>gRPC context propagation</description>
  <licenses>
    <license>
      <name>Apache-2.0</name>
    </license>
  </licenses>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact grpc-context.pom:grpc-context.jar \
	--file-name grpc-context \
	--filelist .mfiles

%check
mkdir -p check
cat > check/Smoke.java << 'END'
import io.grpc.Context;
public class Smoke {
	public static void main(String[] args) {
		Context.Key<String> key = Context.key("check");
		Context ctx = Context.current().withValue(key, "value");
		Context prev = ctx.attach();
		try {
			System.out.println("grpc_context_ok " + key.get());
		} finally {
			ctx.detach(prev);
		}
	}
}
END
JAR=%{buildroot}%{_javadir}/grpc-context.jar
test -f "$JAR"
javac --release 8 -encoding UTF-8 -cp "$JAR" -d check check/Smoke.java
java -cp "check:$JAR" Smoke > check/out.txt
cat check/out.txt
grep -F -q 'grpc_context_ok value' check/out.txt

%files -f .mfiles
%doc LICENSE NOTICE.txt
